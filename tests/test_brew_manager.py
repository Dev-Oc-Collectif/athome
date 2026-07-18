"""Tests for BrewManager — the Homebrew-backed tool manager."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest

from athome.definitions.managers.base import BaseManager
from athome.exceptions import ToolNotFoundError
from athome.tools.managers.brew import BrewManager

_BASE_PATCH = 'athome.definitions.managers.base.shutil.which'


@pytest.fixture
def brew_available() -> Generator[None]:  # type: ignore[return]
    with patch(_BASE_PATCH, return_value='/usr/local/bin/brew'):
        yield


class TestBrewManagerContract:
    def test_is_base_manager(self) -> None:
        assert issubclass(BrewManager, BaseManager)

    def test_instantiates(self, brew_available: None) -> None:
        assert isinstance(BrewManager(), BrewManager)


class TestBrewSync:
    def test_sync_with_brewfile(self, tmp_path: Path, brew_available: None) -> None:
        manifest = tmp_path / 'Brewfile'
        manifest.touch()
        mgr = BrewManager()
        with patch('athome.tools.managers.brew.subprocess.run') as mock_run:
            mgr.sync(manifest)
        cmd = mock_run.call_args[0][0]
        assert cmd == ['brew', 'bundle', 'install', '--file', str(manifest)]

    def test_check_is_true(self, tmp_path: Path, brew_available: None) -> None:
        manifest = tmp_path / 'Brewfile'
        manifest.touch()
        mgr = BrewManager()
        with patch('athome.tools.managers.brew.subprocess.run') as mock_run:
            mgr.sync(manifest)
        assert mock_run.call_args[1].get('check') is True


class TestBrewUpgrade:
    def test_upgrade_all_formulae(self, brew_available: None) -> None:
        mgr = BrewManager()
        with patch('athome.tools.managers.brew.subprocess.run') as mock_run:
            mgr.upgrade()
        assert mock_run.call_args[0][0] == ['brew', 'upgrade']

    def test_upgrade_specific_formula(self, brew_available: None) -> None:
        mgr = BrewManager()
        with patch('athome.tools.managers.brew.subprocess.run') as mock_run:
            mgr.upgrade('git')
        assert mock_run.call_args[0][0] == ['brew', 'upgrade', 'git']


class TestBrewUse:
    def test_installs_versioned_formula(self, brew_available: None) -> None:
        mgr = BrewManager()
        with patch('athome.tools.managers.brew.subprocess.run') as mock_run:
            mgr.use('python', '3.12')
        assert mock_run.call_args[0][0] == ['brew', 'install', 'python@3.12']

    def test_global_scope_ignored(self, brew_available: None) -> None:
        mgr = BrewManager()
        with patch('athome.tools.managers.brew.subprocess.run') as mock_run:
            mgr.use('node', '20', global_scope=True)
        assert mock_run.call_args[0][0] == ['brew', 'install', 'node@20']


class TestBrewListTools:
    def test_calls_brew_list(self, brew_available: None) -> None:
        mgr = BrewManager()
        with patch('athome.tools.managers.brew.subprocess.run') as mock_run:
            mgr.list_tools()
        assert mock_run.call_args[0][0] == ['brew', 'list']


class TestBrewDoctor:
    def test_calls_brew_doctor(self, brew_available: None) -> None:
        mgr = BrewManager()
        with patch('athome.tools.managers.brew.subprocess.run') as mock_run:
            mgr.doctor()
        assert mock_run.call_args[0][0] == ['brew', 'doctor']


class TestBrewCleanup:
    def test_default_is_non_destructive(self, tmp_path: Path, brew_available: None) -> None:
        manifest = tmp_path / 'Brewfile'
        manifest.touch()
        mgr = BrewManager()
        with patch('athome.tools.managers.brew.subprocess.run') as mock_run:
            mgr.cleanup(manifest)
        cmd = mock_run.call_args[0][0]
        assert cmd == ['brew', 'bundle', 'cleanup', f'--file={manifest}']

    def test_force_appends_flag(self, tmp_path: Path, brew_available: None) -> None:
        manifest = tmp_path / 'Brewfile'
        manifest.touch()
        mgr = BrewManager()
        with patch('athome.tools.managers.brew.subprocess.run') as mock_run:
            mgr.cleanup(manifest, force=True)
        cmd = mock_run.call_args[0][0]
        assert cmd == ['brew', 'bundle', 'cleanup', f'--file={manifest}', '--force']


class TestBrewToolNotFound:
    def test_raises_at_instantiation_when_brew_missing(self) -> None:
        with (
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError),
        ):
            BrewManager()

    def test_error_message_names_tool(self) -> None:
        with (
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError) as exc_info,
        ):
            BrewManager()
        assert 'brew' in exc_info.value.format_message()

    def test_error_includes_install_hint(self) -> None:
        with (
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError) as exc_info,
        ):
            BrewManager()
        assert 'brew.sh' in exc_info.value.format_message()

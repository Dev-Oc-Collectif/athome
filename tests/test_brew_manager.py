"""Tests for BrewManager — the Homebrew-backed tool manager."""

from __future__ import annotations

import subprocess
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
            mock_run.return_value.returncode = 0
            mgr.cleanup(manifest)
        cmd = mock_run.call_args[0][0]
        assert cmd == ['brew', 'bundle', 'cleanup', f'--file={manifest}']

    def test_dry_run_exit_1_is_a_report_not_a_failure(
        self, tmp_path: Path, brew_available: None
    ) -> None:
        """`brew bundle cleanup` exits 1 when it listed things to remove."""
        manifest = tmp_path / 'Brewfile'
        manifest.touch()
        mgr = BrewManager()
        with patch('athome.tools.managers.brew.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 1
            mgr.cleanup(manifest)  # must not raise

    def test_dry_run_still_raises_on_a_real_error(
        self, tmp_path: Path, brew_available: None
    ) -> None:
        manifest = tmp_path / 'Brewfile'
        manifest.touch()
        mgr = BrewManager()
        with patch('athome.tools.managers.brew.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 2
            mock_run.return_value.args = ['brew']
            with pytest.raises(subprocess.CalledProcessError):
                mgr.cleanup(manifest)

    def test_force_does_not_tolerate_a_nonzero_exit(
        self, tmp_path: Path, brew_available: None
    ) -> None:
        """With --force, exit 1 means the removal actually failed."""
        manifest = tmp_path / 'Brewfile'
        manifest.touch()
        mgr = BrewManager()
        with (
            patch(
                'athome.tools.managers.brew.subprocess.run',
                side_effect=subprocess.CalledProcessError(1, ['brew']),
            ),
            pytest.raises(subprocess.CalledProcessError),
        ):
            mgr.cleanup(manifest, force=True)

    def test_force_appends_flag(self, tmp_path: Path, brew_available: None) -> None:
        manifest = tmp_path / 'Brewfile'
        manifest.touch()
        mgr = BrewManager()
        with patch('athome.tools.managers.brew.subprocess.run') as mock_run:
            mgr.cleanup(manifest, force=True)
        cmd = mock_run.call_args[0][0]
        assert cmd == ['brew', 'bundle', 'cleanup', f'--file={manifest}', '--force']


class TestBrewToolNotFound:
    def test_instantiation_never_raises_even_when_brew_missing(self) -> None:
        """Constructing a manager must not require its tool to be present.

        athome.cli modules build their managers eagerly at import time, so a
        check here would mean merely importing athome's CLI — e.g. running
        `athome --help` — fails on any machine missing *any* required tool,
        even for a command that never touches this manager.
        """
        with patch(_BASE_PATCH, return_value=None):
            BrewManager()

    def test_raises_on_first_use_when_brew_missing(self) -> None:
        mgr = BrewManager()
        with (
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError),
        ):
            mgr.list_tools()

    def test_error_message_names_tool(self) -> None:
        mgr = BrewManager()
        with (
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError) as exc_info,
        ):
            mgr.list_tools()
        assert 'brew' in exc_info.value.format_message()

    def test_error_includes_install_hint(self) -> None:
        mgr = BrewManager()
        with (
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError) as exc_info,
        ):
            mgr.list_tools()
        assert 'brew.sh' in exc_info.value.format_message()

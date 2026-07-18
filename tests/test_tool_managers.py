"""Tests for ToolManager implementations — MiseToolManager and BrewToolManager."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest

from athome.definitions.managers.tool import ToolManager
from athome.exceptions import ToolNotFoundError
from athome.tools.managers.brew import BrewToolManager
from athome.tools.managers.mise import MiseToolManager

_BASE_PATCH = 'athome.interfaces.base.shutil.which'


# ---------------------------------------------------------------------------
# MiseToolManager
# ---------------------------------------------------------------------------


@pytest.fixture
def mise_available() -> Generator[None]:  # type: ignore[return]
    with patch(_BASE_PATCH, return_value='/usr/bin/mise'):
        yield


class TestMiseToolManagerContract:
    def test_is_tool_manager(self) -> None:
        assert issubclass(MiseToolManager, ToolManager)

    def test_instantiates(self, mise_available: None) -> None:
        assert isinstance(MiseToolManager(), MiseToolManager)


class TestMiseSync:
    def test_sync_with_manifest(self, tmp_path: Path, mise_available: None) -> None:
        manifest = tmp_path / 'mise.toml'
        manifest.touch()
        mgr = MiseToolManager()
        with patch('athome.tool_managers.mise.subprocess.run') as mock_run:
            mgr.sync(manifest)
        cmd = mock_run.call_args[0][0]
        assert cmd == ['mise', 'install', '--config', str(manifest)]

    def test_check_is_true(self, tmp_path: Path, mise_available: None) -> None:
        manifest = tmp_path / 'mise.toml'
        manifest.touch()
        mgr = MiseToolManager()
        with patch('athome.tool_managers.mise.subprocess.run') as mock_run:
            mgr.sync(manifest)
        assert mock_run.call_args[1].get('check') is True


class TestMiseUpgrade:
    def test_upgrade_all_tools(self, mise_available: None) -> None:
        mgr = MiseToolManager()
        with patch('athome.tool_managers.mise.subprocess.run') as mock_run:
            mgr.upgrade()
        cmd = mock_run.call_args[0][0]
        assert cmd == ['mise', 'upgrade', '--yes']

    def test_upgrade_specific_tool(self, mise_available: None) -> None:
        mgr = MiseToolManager()
        with patch('athome.tool_managers.mise.subprocess.run') as mock_run:
            mgr.upgrade('node')
        cmd = mock_run.call_args[0][0]
        assert cmd == ['mise', 'upgrade', '--yes', 'node']


class TestMiseUse:
    def test_use_local_by_default(self, mise_available: None) -> None:
        mgr = MiseToolManager()
        with patch('athome.tool_managers.mise.subprocess.run') as mock_run:
            mgr.use('python', '3.12')
        cmd = mock_run.call_args[0][0]
        assert cmd == ['mise', 'use', '--local', 'python@3.12']

    def test_use_global_scope(self, mise_available: None) -> None:
        mgr = MiseToolManager()
        with patch('athome.tool_managers.mise.subprocess.run') as mock_run:
            mgr.use('python', '3.12', global_scope=True)
        cmd = mock_run.call_args[0][0]
        assert cmd == ['mise', 'use', '--global', 'python@3.12']

    def test_version_pinned_with_at_sign(self, mise_available: None) -> None:
        mgr = MiseToolManager()
        with patch('athome.tool_managers.mise.subprocess.run') as mock_run:
            mgr.use('node', '20')
        assert 'node@20' in mock_run.call_args[0][0]


class TestMiseListTools:
    def test_calls_mise_list(self, mise_available: None) -> None:
        mgr = MiseToolManager()
        with patch('athome.tool_managers.mise.subprocess.run') as mock_run:
            mgr.list_tools()
        assert mock_run.call_args[0][0] == ['mise', 'list']


class TestMiseDoctor:
    def test_calls_mise_doctor(self, mise_available: None) -> None:
        mgr = MiseToolManager()
        with patch('athome.tool_managers.mise.subprocess.run') as mock_run:
            mgr.doctor()
        assert mock_run.call_args[0][0] == ['mise', 'doctor']


class TestMiseToolNotFound:
    def test_raises_at_instantiation_when_mise_missing(self) -> None:
        with (
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError),
        ):
            MiseToolManager()

    def test_error_message_names_tool(self) -> None:
        with (
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError) as exc_info,
        ):
            MiseToolManager()
        assert 'mise' in exc_info.value.format_message()

    def test_error_includes_install_hint(self) -> None:
        with (
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError) as exc_info,
        ):
            MiseToolManager()
        assert 'mise.jdx.dev' in exc_info.value.format_message()


# ---------------------------------------------------------------------------
# BrewToolManager
# ---------------------------------------------------------------------------


@pytest.fixture
def brew_available() -> Generator[None]:  # type: ignore[return]
    with patch(_BASE_PATCH, return_value='/usr/local/bin/brew'):
        yield


class TestBrewToolManagerContract:
    def test_is_tool_manager(self) -> None:
        assert issubclass(BrewToolManager, ToolManager)

    def test_instantiates(self, brew_available: None) -> None:
        assert isinstance(BrewToolManager(), BrewToolManager)


class TestBrewSync:
    def test_sync_with_brewfile(self, tmp_path: Path, brew_available: None) -> None:
        manifest = tmp_path / 'Brewfile'
        manifest.touch()
        mgr = BrewToolManager()
        with patch('athome.tool_managers.brew.subprocess.run') as mock_run:
            mgr.sync(manifest)
        cmd = mock_run.call_args[0][0]
        assert cmd == ['brew', 'bundle', 'install', '--file', str(manifest)]

    def test_check_is_true(self, tmp_path: Path, brew_available: None) -> None:
        manifest = tmp_path / 'Brewfile'
        manifest.touch()
        mgr = BrewToolManager()
        with patch('athome.tool_managers.brew.subprocess.run') as mock_run:
            mgr.sync(manifest)
        assert mock_run.call_args[1].get('check') is True


class TestBrewUpgrade:
    def test_upgrade_all_formulae(self, brew_available: None) -> None:
        mgr = BrewToolManager()
        with patch('athome.tool_managers.brew.subprocess.run') as mock_run:
            mgr.upgrade()
        assert mock_run.call_args[0][0] == ['brew', 'upgrade']

    def test_upgrade_specific_formula(self, brew_available: None) -> None:
        mgr = BrewToolManager()
        with patch('athome.tool_managers.brew.subprocess.run') as mock_run:
            mgr.upgrade('git')
        assert mock_run.call_args[0][0] == ['brew', 'upgrade', 'git']


class TestBrewUse:
    def test_installs_versioned_formula(self, brew_available: None) -> None:
        mgr = BrewToolManager()
        with patch('athome.tool_managers.brew.subprocess.run') as mock_run:
            mgr.use('python', '3.12')
        assert mock_run.call_args[0][0] == ['brew', 'install', 'python@3.12']

    def test_global_scope_ignored(self, brew_available: None) -> None:
        mgr = BrewToolManager()
        with patch('athome.tool_managers.brew.subprocess.run') as mock_run:
            mgr.use('node', '20', global_scope=True)
        assert mock_run.call_args[0][0] == ['brew', 'install', 'node@20']


class TestBrewListTools:
    def test_calls_brew_list(self, brew_available: None) -> None:
        mgr = BrewToolManager()
        with patch('athome.tool_managers.brew.subprocess.run') as mock_run:
            mgr.list_tools()
        assert mock_run.call_args[0][0] == ['brew', 'list']


class TestBrewDoctor:
    def test_calls_brew_doctor(self, brew_available: None) -> None:
        mgr = BrewToolManager()
        with patch('athome.tool_managers.brew.subprocess.run') as mock_run:
            mgr.doctor()
        assert mock_run.call_args[0][0] == ['brew', 'doctor']


class TestBrewToolNotFound:
    def test_raises_at_instantiation_when_brew_missing(self) -> None:
        with (
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError),
        ):
            BrewToolManager()

    def test_error_message_names_tool(self) -> None:
        with (
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError) as exc_info,
        ):
            BrewToolManager()
        assert 'brew' in exc_info.value.format_message()

    def test_error_includes_install_hint(self) -> None:
        with (
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError) as exc_info,
        ):
            BrewToolManager()
        assert 'brew.sh' in exc_info.value.format_message()

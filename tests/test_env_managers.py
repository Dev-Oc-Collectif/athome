"""Tests for MiseManager — EnvManager backed by mise."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

import pytest

from athome.env_managers.mise import MiseManager
from athome.exceptions import ToolNotFoundError
from athome.interfaces.env_manager import EnvManager


@pytest.fixture(autouse=True)
def mise_available() -> Generator[None]:  # type: ignore[return]
    with patch('athome.env_managers.mise.shutil.which', return_value='/usr/bin/mise'):
        yield


class TestMiseManagerContract:
    def test_is_env_manager(self) -> None:
        assert issubclass(MiseManager, EnvManager)

    def test_instantiates(self) -> None:
        assert isinstance(MiseManager(), MiseManager)


class TestInstall:
    def test_install_without_version(self) -> None:
        mgr = MiseManager()
        with patch('athome.env_managers.mise.subprocess.run') as mock_run:
            mgr.install('python')
        cmd = mock_run.call_args[0][0]
        assert cmd == ['mise', 'install', 'python']

    def test_install_with_version(self) -> None:
        mgr = MiseManager()
        with patch('athome.env_managers.mise.subprocess.run') as mock_run:
            mgr.install('python', '3.12')
        cmd = mock_run.call_args[0][0]
        assert cmd == ['mise', 'install', 'python@3.12']

    def test_check_is_true(self) -> None:
        mgr = MiseManager()
        with patch('athome.env_managers.mise.subprocess.run') as mock_run:
            mgr.install('node')
        assert mock_run.call_args[1].get('check') is True


class TestUpgrade:
    def test_upgrade_all_tools(self) -> None:
        mgr = MiseManager()
        with patch('athome.env_managers.mise.subprocess.run') as mock_run:
            mgr.upgrade()
        cmd = mock_run.call_args[0][0]
        assert cmd == ['mise', 'upgrade', '--yes']

    def test_upgrade_specific_tool(self) -> None:
        mgr = MiseManager()
        with patch('athome.env_managers.mise.subprocess.run') as mock_run:
            mgr.upgrade('node')
        cmd = mock_run.call_args[0][0]
        assert cmd == ['mise', 'upgrade', '--yes', 'node']


class TestUse:
    def test_use_local_by_default(self) -> None:
        mgr = MiseManager()
        with patch('athome.env_managers.mise.subprocess.run') as mock_run:
            mgr.use('python', '3.12')
        cmd = mock_run.call_args[0][0]
        assert cmd == ['mise', 'use', '--local', 'python@3.12']

    def test_use_global_scope(self) -> None:
        mgr = MiseManager()
        with patch('athome.env_managers.mise.subprocess.run') as mock_run:
            mgr.use('python', '3.12', global_scope=True)
        cmd = mock_run.call_args[0][0]
        assert cmd == ['mise', 'use', '--global', 'python@3.12']

    def test_version_is_pinned_with_at_sign(self) -> None:
        mgr = MiseManager()
        with patch('athome.env_managers.mise.subprocess.run') as mock_run:
            mgr.use('node', '20')
        cmd = mock_run.call_args[0][0]
        assert 'node@20' in cmd


class TestListTools:
    def test_calls_mise_list(self) -> None:
        mgr = MiseManager()
        with patch('athome.env_managers.mise.subprocess.run') as mock_run:
            mgr.list_tools()
        cmd = mock_run.call_args[0][0]
        assert cmd == ['mise', 'list']


class TestDoctor:
    def test_calls_mise_doctor(self) -> None:
        mgr = MiseManager()
        with patch('athome.env_managers.mise.subprocess.run') as mock_run:
            mgr.doctor()
        cmd = mock_run.call_args[0][0]
        assert cmd == ['mise', 'doctor']


class TestToolNotFound:
    def test_install_raises_when_mise_missing(self) -> None:
        mgr = MiseManager()
        with (
            patch('athome.env_managers.mise.shutil.which', return_value=None),
            pytest.raises(ToolNotFoundError),
        ):
            mgr.install('python')

    def test_error_message_names_tool(self) -> None:
        mgr = MiseManager()
        with (
            patch('athome.env_managers.mise.shutil.which', return_value=None),
            pytest.raises(ToolNotFoundError) as exc_info,
        ):
            mgr.install('python')
        assert 'mise' in exc_info.value.format_message()

    def test_error_includes_install_hint(self) -> None:
        mgr = MiseManager()
        with (
            patch('athome.env_managers.mise.shutil.which', return_value=None),
            pytest.raises(ToolNotFoundError) as exc_info,
        ):
            mgr.upgrade()
        assert 'mise.jdx.dev' in exc_info.value.format_message()

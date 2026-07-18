"""Tests for EnvManager implementations — DirenvManager and MiseEnvManager."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

import pytest

from athome.contexts.managers.direnv import DirenvManager
from athome.contexts.managers.mise import MiseEnvManager
from athome.definitions.managers.context import ContextManager
from athome.exceptions import ToolNotFoundError

_BASE_PATCH = 'athome.interfaces.base.shutil.which'


# ---------------------------------------------------------------------------
# DirenvManager
# ---------------------------------------------------------------------------


@pytest.fixture
def direnv_available() -> Generator[None]:  # type: ignore[return]
    with patch(_BASE_PATCH, return_value='/usr/bin/direnv'):
        yield


class TestDirenvManagerContract:
    def test_is_env_manager(self) -> None:
        assert issubclass(DirenvManager, ContextManager)

    def test_instantiates(self, direnv_available: None) -> None:
        assert isinstance(DirenvManager(), DirenvManager)


class TestDirenvLoad:
    def test_allows_envrc(self, direnv_available: None) -> None:
        mgr = DirenvManager()
        with patch('athome.env_managers.direnv.subprocess.run') as mock_run:
            mgr.load()
        calls = [c[0][0] for c in mock_run.call_args_list]
        assert ['direnv', 'allow'] in calls

    def test_evals_envrc(self, direnv_available: None) -> None:
        mgr = DirenvManager()
        with patch('athome.env_managers.direnv.subprocess.run') as mock_run:
            mgr.load()
        calls = [c[0][0] for c in mock_run.call_args_list]
        assert ['direnv', 'exec', '.', 'true'] in calls


class TestDirenvActivate:
    def test_defaults_to_bash(self, direnv_available: None) -> None:
        mgr = DirenvManager()
        with patch('athome.env_managers.direnv.subprocess.run') as mock_run:
            mgr.activate()
        assert mock_run.call_args[0][0] == ['direnv', 'hook', 'bash']

    def test_uses_given_shell(self, direnv_available: None) -> None:
        mgr = DirenvManager()
        with patch('athome.env_managers.direnv.subprocess.run') as mock_run:
            mgr.activate('zsh')
        assert mock_run.call_args[0][0] == ['direnv', 'hook', 'zsh']

    def test_fish_shell(self, direnv_available: None) -> None:
        mgr = DirenvManager()
        with patch('athome.env_managers.direnv.subprocess.run') as mock_run:
            mgr.activate('fish')
        assert mock_run.call_args[0][0] == ['direnv', 'hook', 'fish']


class TestDirenvNotFound:
    def test_raises_when_direnv_missing(self) -> None:
        with (
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError),
        ):
            DirenvManager()

    def test_error_names_tool(self) -> None:
        with (
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError) as exc_info,
        ):
            DirenvManager()
        assert 'direnv' in exc_info.value.format_message()

    def test_error_includes_install_hint(self) -> None:
        with (
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError) as exc_info,
        ):
            DirenvManager()
        assert 'direnv.net' in exc_info.value.format_message()


# ---------------------------------------------------------------------------
# MiseEnvManager
# ---------------------------------------------------------------------------


@pytest.fixture
def mise_available() -> Generator[None]:  # type: ignore[return]
    with patch(_BASE_PATCH, return_value='/usr/bin/mise'):
        yield


class TestMiseEnvManagerContract:
    def test_is_env_manager(self) -> None:
        assert issubclass(MiseEnvManager, ContextManager)

    def test_instantiates(self, mise_available: None) -> None:
        assert isinstance(MiseEnvManager(), MiseEnvManager)


class TestMiseEnvLoad:
    def test_calls_mise_trust(self, mise_available: None) -> None:
        mgr = MiseEnvManager()
        with patch('athome.env_managers.mise.subprocess.run') as mock_run:
            mgr.load()
        assert mock_run.call_args[0][0] == ['mise', 'trust']

    def test_check_is_true(self, mise_available: None) -> None:
        mgr = MiseEnvManager()
        with patch('athome.env_managers.mise.subprocess.run') as mock_run:
            mgr.load()
        assert mock_run.call_args[1].get('check') is True


class TestMiseEnvActivate:
    def test_defaults_to_bash(self, mise_available: None) -> None:
        mgr = MiseEnvManager()
        with patch('athome.env_managers.mise.subprocess.run') as mock_run:
            mgr.activate()
        assert mock_run.call_args[0][0] == ['mise', 'activate', 'bash']

    def test_uses_given_shell(self, mise_available: None) -> None:
        mgr = MiseEnvManager()
        with patch('athome.env_managers.mise.subprocess.run') as mock_run:
            mgr.activate('zsh')
        assert mock_run.call_args[0][0] == ['mise', 'activate', 'zsh']

    def test_fish_shell(self, mise_available: None) -> None:
        mgr = MiseEnvManager()
        with patch('athome.env_managers.mise.subprocess.run') as mock_run:
            mgr.activate('fish')
        assert mock_run.call_args[0][0] == ['mise', 'activate', 'fish']


class TestMiseEnvNotFound:
    def test_raises_when_mise_missing(self) -> None:
        with (
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError),
        ):
            MiseEnvManager()

    def test_error_names_tool(self) -> None:
        with (
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError) as exc_info,
        ):
            MiseEnvManager()
        assert 'mise' in exc_info.value.format_message()

    def test_error_includes_install_hint(self) -> None:
        with (
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError) as exc_info,
        ):
            MiseEnvManager()
        assert 'mise.jdx.dev' in exc_info.value.format_message()

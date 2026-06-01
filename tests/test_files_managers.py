"""Tests for ChezmoidManager — SharedFileManager backed by chezmoi."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest

from athome.config import ProfileConfig
from athome.config import profile_config_path
from athome.config import profile_source_path
from athome.config import profile_state_path
from athome.exceptions import ToolNotFoundError
from athome.files_managers.chezmoi import ChezmoidManager
from athome.interfaces.shared_file_manager import SharedFileManager


@pytest.fixture(autouse=True)
def chezmoi_available() -> Generator[None]:
    with patch('athome.files_managers.chezmoi.shutil.which', return_value='/usr/bin/chezmoi'):
        yield


PROFILE = ProfileConfig(name='work', source='https://github.com/org/dotfiles-work')
PROFILE_B = ProfileConfig(name='personal', source='https://github.com/user/dotfiles')


def expected_flags(profile: ProfileConfig) -> list[str]:
    return [
        f'--source={profile_source_path(profile)}',
        f'--config={profile_config_path(profile.name)}',
        f'--state={profile_state_path(profile.name)}',
    ]


class TestChezmoidManagerContract:
    def test_is_shared_file_manager(self) -> None:
        assert issubclass(ChezmoidManager, SharedFileManager)

    def test_instantiates(self) -> None:
        assert isinstance(ChezmoidManager(), ChezmoidManager)


class TestProfileFlags:
    def test_flags_contain_source(self) -> None:
        mgr = ChezmoidManager()
        flags = mgr._profile_flags(PROFILE)
        assert any('--source=' in f for f in flags)

    def test_flags_contain_config(self) -> None:
        mgr = ChezmoidManager()
        flags = mgr._profile_flags(PROFILE)
        assert any('--config=' in f for f in flags)

    def test_flags_contain_state(self) -> None:
        mgr = ChezmoidManager()
        flags = mgr._profile_flags(PROFILE)
        assert any('--state=' in f for f in flags)

    def test_flags_embed_profile_name_in_paths(self) -> None:
        mgr = ChezmoidManager()
        flags = mgr._profile_flags(PROFILE)
        assert all(PROFILE.name in f for f in flags)

    def test_different_profiles_yield_different_flags(self) -> None:
        mgr = ChezmoidManager()
        assert mgr._profile_flags(PROFILE) != mgr._profile_flags(PROFILE_B)

    def test_custom_destination_used_in_source_flag(self) -> None:
        custom = Path('/custom/dots')
        profile = ProfileConfig(name='dev', source='url', destination=custom)
        mgr = ChezmoidManager()
        flags = mgr._profile_flags(profile)
        assert f'--source={custom}' in flags


class TestSync:
    def test_calls_chezmoi_update(self) -> None:
        mgr = ChezmoidManager()
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mgr.sync(PROFILE)
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == 'chezmoi'
        assert 'update' in cmd

    def test_passes_profile_flags(self) -> None:
        mgr = ChezmoidManager()
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mgr.sync(PROFILE)
        cmd = mock_run.call_args[0][0]
        assert f'--source={profile_source_path(PROFILE)}' in cmd

    def test_check_is_true(self) -> None:
        mgr = ChezmoidManager()
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mgr.sync(PROFILE)
        assert mock_run.call_args[1].get('check') is True


class TestApply:
    def test_calls_chezmoi_apply(self) -> None:
        mgr = ChezmoidManager()
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mgr.apply(PROFILE)
        cmd = mock_run.call_args[0][0]
        assert 'apply' in cmd

    def test_passes_profile_flags(self) -> None:
        mgr = ChezmoidManager()
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mgr.apply(PROFILE)
        cmd = mock_run.call_args[0][0]
        assert f'--config={profile_config_path(PROFILE.name)}' in cmd


class TestAdd:
    def test_calls_chezmoi_add_with_path(self) -> None:
        mgr = ChezmoidManager()
        target = Path('/home/user/.zshrc')
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mgr.add(PROFILE, target)
        cmd = mock_run.call_args[0][0]
        assert 'add' in cmd
        assert str(target) in cmd

    def test_path_is_stringified(self) -> None:
        mgr = ChezmoidManager()
        target = Path('/some/file')
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mgr.add(PROFILE, target)
        cmd = mock_run.call_args[0][0]
        assert '/some/file' in cmd


class TestDiff:
    def test_calls_chezmoi_diff(self) -> None:
        mgr = ChezmoidManager()
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mgr.diff(PROFILE)
        cmd = mock_run.call_args[0][0]
        assert 'diff' in cmd


class TestStatus:
    def test_calls_chezmoi_status(self) -> None:
        mgr = ChezmoidManager()
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mgr.status(PROFILE)
        cmd = mock_run.call_args[0][0]
        assert 'status' in cmd


class TestToolNotFound:
    def test_sync_raises_when_chezmoi_missing(self) -> None:
        mgr = ChezmoidManager()
        with (
            patch('athome.files_managers.chezmoi.shutil.which', return_value=None),
            pytest.raises(ToolNotFoundError),
        ):
            mgr.sync(PROFILE)

    def test_error_message_names_tool(self) -> None:
        mgr = ChezmoidManager()
        with (
            patch('athome.files_managers.chezmoi.shutil.which', return_value=None),
            pytest.raises(ToolNotFoundError) as exc_info,
        ):
            mgr.sync(PROFILE)
        assert 'chezmoi' in exc_info.value.format_message()

    def test_error_includes_install_hint(self) -> None:
        mgr = ChezmoidManager()
        with (
            patch('athome.files_managers.chezmoi.shutil.which', return_value=None),
            pytest.raises(ToolNotFoundError) as exc_info,
        ):
            mgr.apply(PROFILE)
        assert 'chezmoi.io' in exc_info.value.format_message()

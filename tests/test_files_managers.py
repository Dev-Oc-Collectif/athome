"""Tests for ChezmoiManager — SharedFileManager backed by chezmoi."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest

from athome.definitions.config import ProfileConfig
from athome.definitions.config import profile_config_path
from athome.definitions.config import profile_source_path
from athome.definitions.managers.base import BaseManager
from athome.exceptions import ToolNotFoundError
from athome.profiles.managers.chezmoi import ChezmoiManager

_BASE_PATCH = 'athome.definitions.managers.base.shutil.which'


@pytest.fixture(autouse=True)
def chezmoi_available() -> Generator[None]:
    with patch(_BASE_PATCH, return_value='/usr/bin/chezmoi'):
        yield


PROFILE = ProfileConfig(name='work', source='https://github.com/org/dotfiles-work')
PROFILE_B = ProfileConfig(name='personal', source='https://github.com/user/dotfiles')


class TestChezmoiManagerContract:
    def test_is_shared_file_manager(self) -> None:
        assert issubclass(ChezmoiManager, BaseManager)

    def test_instantiates(self) -> None:
        assert isinstance(ChezmoiManager(), ChezmoiManager)


class TestProfileFlags:
    def test_flags_contain_source(self) -> None:
        mgr = ChezmoiManager()
        flags = mgr._profile_flags(PROFILE)
        assert any('--source=' in f for f in flags)

    def test_flags_contain_config(self) -> None:
        mgr = ChezmoiManager()
        flags = mgr._profile_flags(PROFILE)
        assert any('--config=' in f for f in flags)

    def test_flags_contain_state(self) -> None:
        mgr = ChezmoiManager()
        flags = mgr._profile_flags(PROFILE)
        assert any('--persistent-state=' in f for f in flags)

    def test_flags_embed_profile_name_in_paths(self) -> None:
        mgr = ChezmoiManager()
        flags = mgr._profile_flags(PROFILE)
        assert all(PROFILE.name in f for f in flags)

    def test_different_profiles_yield_different_flags(self) -> None:
        mgr = ChezmoiManager()
        assert mgr._profile_flags(PROFILE) != mgr._profile_flags(PROFILE_B)

    def test_custom_destination_used_in_source_flag(self) -> None:
        custom = Path('/custom/dots')
        profile = ProfileConfig(name='dev', source='url', destination=custom)
        mgr = ChezmoiManager()
        flags = mgr._profile_flags(profile)
        assert f'--source={custom}' in flags


class TestIsInitialized:
    def test_returns_true_when_source_dir_is_a_git_checkout(self, tmp_path: Path) -> None:
        source = tmp_path / 'work'
        (source / '.git').mkdir(parents=True)
        profile = ProfileConfig(name='work', source='url', destination=source)
        assert ChezmoiManager().is_initialized(profile) is True

    def test_returns_false_when_source_dir_missing(self, tmp_path: Path) -> None:
        source = tmp_path / 'work'
        profile = ProfileConfig(name='work', source='url', destination=source)
        assert ChezmoiManager().is_initialized(profile) is False

    def test_returns_false_when_source_dir_exists_but_empty(self, tmp_path: Path) -> None:
        """A partial/failed init can leave an empty dir behind — must not read as done."""
        source = tmp_path / 'work'
        source.mkdir()
        profile = ProfileConfig(name='work', source='url', destination=source)
        assert ChezmoiManager().is_initialized(profile) is False


class TestInit:
    def test_calls_chezmoi_init_with_source_url(self) -> None:
        mgr = ChezmoiManager()
        with (
            patch('athome.profiles.managers.chezmoi.subprocess.run') as mock_run,
            patch('athome.profiles.managers.chezmoi.Path.mkdir'),
        ):
            mgr.init(PROFILE)
        cmd = mock_run.call_args[0][0]
        assert 'init' in cmd
        assert PROFILE.source in cmd

    def test_passes_no_apply_flag(self) -> None:
        mgr = ChezmoiManager()
        with (
            patch('athome.profiles.managers.chezmoi.subprocess.run') as mock_run,
            patch('athome.profiles.managers.chezmoi.Path.mkdir'),
        ):
            mgr.init(PROFILE)
        cmd = mock_run.call_args[0][0]
        assert '--apply=false' in cmd

    def test_passes_profile_flags(self) -> None:
        mgr = ChezmoiManager()
        with (
            patch('athome.profiles.managers.chezmoi.subprocess.run') as mock_run,
            patch('athome.profiles.managers.chezmoi.Path.mkdir'),
        ):
            mgr.init(PROFILE)
        cmd = mock_run.call_args[0][0]
        assert f'--source={profile_source_path(PROFILE)}' in cmd

    def test_creates_config_parent_dir(self, tmp_path: Path) -> None:
        config_dir = tmp_path / 'profiles'
        profile = ProfileConfig(name='test', source='url', destination=tmp_path / 'src')
        with (
            patch('athome.profiles.managers.chezmoi.subprocess.run'),
            patch(
                'athome.profiles.managers.chezmoi.profile_config_path',
                return_value=config_dir / 'test.toml',
            ),
            patch(
                'athome.profiles.managers.chezmoi.profile_source_path',
                return_value=tmp_path / 'src',
            ),
        ):
            ChezmoiManager().init(profile)
        assert config_dir.exists()

    def test_raises_when_chezmoi_missing(self) -> None:
        mgr = ChezmoiManager()
        with (
            patch('athome.profiles.managers.chezmoi.Path.mkdir'),
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError),
        ):
            mgr.init(PROFILE)


class TestSync:
    def test_calls_chezmoi_update(self) -> None:
        mgr = ChezmoiManager()
        with patch('athome.profiles.managers.chezmoi.subprocess.run') as mock_run:
            mgr.sync(PROFILE)
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == 'chezmoi'
        assert 'update' in cmd

    def test_passes_profile_flags(self) -> None:
        mgr = ChezmoiManager()
        with patch('athome.profiles.managers.chezmoi.subprocess.run') as mock_run:
            mgr.sync(PROFILE)
        cmd = mock_run.call_args[0][0]
        assert f'--source={profile_source_path(PROFILE)}' in cmd

    def test_check_is_true(self) -> None:
        mgr = ChezmoiManager()
        with patch('athome.profiles.managers.chezmoi.subprocess.run') as mock_run:
            mgr.sync(PROFILE)
        assert mock_run.call_args[1].get('check') is True


class TestApply:
    def test_calls_chezmoi_apply(self) -> None:
        mgr = ChezmoiManager()
        with patch('athome.profiles.managers.chezmoi.subprocess.run') as mock_run:
            mgr.apply(PROFILE)
        cmd = mock_run.call_args[0][0]
        assert 'apply' in cmd

    def test_passes_profile_flags(self) -> None:
        mgr = ChezmoiManager()
        with patch('athome.profiles.managers.chezmoi.subprocess.run') as mock_run:
            mgr.apply(PROFILE)
        cmd = mock_run.call_args[0][0]
        assert f'--config={profile_config_path(PROFILE.name)}' in cmd


class TestAdd:
    def test_calls_chezmoi_add_with_path(self) -> None:
        mgr = ChezmoiManager()
        target = Path('/home/user/.zshrc')
        with patch('athome.profiles.managers.chezmoi.subprocess.run') as mock_run:
            mgr.add(PROFILE, target)
        cmd = mock_run.call_args[0][0]
        assert 'add' in cmd
        assert str(target) in cmd

    def test_path_is_stringified(self) -> None:
        mgr = ChezmoiManager()
        target = Path('/some/file')
        with patch('athome.profiles.managers.chezmoi.subprocess.run') as mock_run:
            mgr.add(PROFILE, target)
        cmd = mock_run.call_args[0][0]
        assert '/some/file' in cmd


class TestDiff:
    def test_calls_chezmoi_diff(self) -> None:
        mgr = ChezmoiManager()
        with patch('athome.profiles.managers.chezmoi.subprocess.run') as mock_run:
            mgr.diff(PROFILE)
        cmd = mock_run.call_args[0][0]
        assert 'diff' in cmd


class TestStatus:
    def test_calls_chezmoi_status(self) -> None:
        mgr = ChezmoiManager()
        with patch('athome.profiles.managers.chezmoi.subprocess.run') as mock_run:
            mgr.status(PROFILE)
        cmd = mock_run.call_args[0][0]
        assert 'status' in cmd


class TestManaged:
    def test_calls_chezmoi_managed_with_files_only(self) -> None:
        mgr = ChezmoiManager()
        with patch('athome.profiles.managers.chezmoi.subprocess.run') as mock_run:
            mock_run.return_value.stdout = ''
            mgr.managed(PROFILE)
        cmd = mock_run.call_args[0][0]
        assert 'managed' in cmd
        assert '--include=files' in cmd
        assert '--path-style=relative' in cmd

    def test_returns_stdout_lines(self) -> None:
        mgr = ChezmoiManager()
        with patch('athome.profiles.managers.chezmoi.subprocess.run') as mock_run:
            mock_run.return_value.stdout = '.zshrc\n.gitconfig\n'
            result = mgr.managed(PROFILE)
        assert result == ['.zshrc', '.gitconfig']

    def test_empty_output_yields_empty_list(self) -> None:
        mgr = ChezmoiManager()
        with patch('athome.profiles.managers.chezmoi.subprocess.run') as mock_run:
            mock_run.return_value.stdout = ''
            result = mgr.managed(PROFILE)
        assert result == []


class TestToolNotFound:
    def test_instantiation_never_raises_even_when_chezmoi_missing(self) -> None:
        """See TestBrewToolNotFound in test_brew_manager.py for why."""
        with patch(_BASE_PATCH, return_value=None):
            ChezmoiManager()

    def test_raises_on_first_use_when_chezmoi_missing(self) -> None:
        mgr = ChezmoiManager()
        with (
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError),
        ):
            mgr.status(PROFILE)

    def test_error_message_names_tool(self) -> None:
        mgr = ChezmoiManager()
        with (
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError) as exc_info,
        ):
            mgr.status(PROFILE)
        assert 'chezmoi' in exc_info.value.format_message()

    def test_error_includes_install_hint(self) -> None:
        mgr = ChezmoiManager()
        with (
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError) as exc_info,
        ):
            mgr.status(PROFILE)
        assert 'chezmoi.io' in exc_info.value.format_message()

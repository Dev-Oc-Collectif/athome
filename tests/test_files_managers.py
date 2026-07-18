"""Tests for ChezmoiManager — SharedFileManager backed by chezmoi."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest

from athome.definitions.config import ProfileConfig
from athome.definitions.config import profile_config_path
from athome.definitions.config import profile_source_path
from athome.definitions.managers.profile import ProfileManager
from athome.exceptions import ToolNotFoundError
from athome.profiles.managers.chezmoi import ChezmoiManager

_BASE_PATCH = 'athome.interfaces.base.shutil.which'


@pytest.fixture(autouse=True)
def chezmoi_available() -> Generator[None]:
    with patch(_BASE_PATCH, return_value='/usr/bin/chezmoi'):
        yield


PROFILE = ProfileConfig(name='work', source='https://github.com/org/dotfiles-work')
PROFILE_B = ProfileConfig(name='personal', source='https://github.com/user/dotfiles')


class TestChezmoiManagerContract:
    def test_is_shared_file_manager(self) -> None:
        assert issubclass(ChezmoiManager, ProfileManager)

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
    def test_returns_true_when_source_dir_exists(self, tmp_path: Path) -> None:
        source = tmp_path / 'work'
        source.mkdir()
        profile = ProfileConfig(name='work', source='url', destination=source)
        assert ChezmoiManager().is_initialized(profile) is True

    def test_returns_false_when_source_dir_missing(self, tmp_path: Path) -> None:
        source = tmp_path / 'work'
        profile = ProfileConfig(name='work', source='url', destination=source)
        assert ChezmoiManager().is_initialized(profile) is False


class TestInit:
    def test_calls_chezmoi_init_with_source_url(self) -> None:
        mgr = ChezmoiManager()
        with (
            patch('athome.files_managers.chezmoi.subprocess.run') as mock_run,
            patch('athome.files_managers.chezmoi.Path.mkdir'),
        ):
            mgr.init(PROFILE)
        cmd = mock_run.call_args[0][0]
        assert 'init' in cmd
        assert PROFILE.source in cmd

    def test_passes_no_apply_flag(self) -> None:
        mgr = ChezmoiManager()
        with (
            patch('athome.files_managers.chezmoi.subprocess.run') as mock_run,
            patch('athome.files_managers.chezmoi.Path.mkdir'),
        ):
            mgr.init(PROFILE)
        cmd = mock_run.call_args[0][0]
        assert '--apply=false' in cmd

    def test_passes_profile_flags(self) -> None:
        mgr = ChezmoiManager()
        with (
            patch('athome.files_managers.chezmoi.subprocess.run') as mock_run,
            patch('athome.files_managers.chezmoi.Path.mkdir'),
        ):
            mgr.init(PROFILE)
        cmd = mock_run.call_args[0][0]
        assert f'--source={profile_source_path(PROFILE)}' in cmd

    def test_creates_config_parent_dir(self, tmp_path: Path) -> None:
        config_dir = tmp_path / 'profiles'
        profile = ProfileConfig(name='test', source='url', destination=tmp_path / 'src')
        with (
            patch('athome.files_managers.chezmoi.subprocess.run'),
            patch(
                'athome.files_managers.chezmoi.profile_config_path',
                return_value=config_dir / 'test.toml',
            ),
            patch(
                'athome.files_managers.chezmoi.profile_source_path',
                return_value=tmp_path / 'src',
            ),
        ):
            ChezmoiManager().init(profile)
        assert config_dir.exists()

    def test_raises_when_chezmoi_missing(self) -> None:
        with (
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError),
        ):
            ChezmoiManager()


class TestSync:
    def test_calls_chezmoi_update(self) -> None:
        mgr = ChezmoiManager()
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mgr.sync(PROFILE)
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == 'chezmoi'
        assert 'update' in cmd

    def test_passes_profile_flags(self) -> None:
        mgr = ChezmoiManager()
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mgr.sync(PROFILE)
        cmd = mock_run.call_args[0][0]
        assert f'--source={profile_source_path(PROFILE)}' in cmd

    def test_check_is_true(self) -> None:
        mgr = ChezmoiManager()
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mgr.sync(PROFILE)
        assert mock_run.call_args[1].get('check') is True


class TestApply:
    def test_calls_chezmoi_apply(self) -> None:
        mgr = ChezmoiManager()
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mgr.apply(PROFILE)
        cmd = mock_run.call_args[0][0]
        assert 'apply' in cmd

    def test_passes_profile_flags(self) -> None:
        mgr = ChezmoiManager()
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mgr.apply(PROFILE)
        cmd = mock_run.call_args[0][0]
        assert f'--config={profile_config_path(PROFILE.name)}' in cmd


class TestAdd:
    def test_calls_chezmoi_add_with_path(self) -> None:
        mgr = ChezmoiManager()
        target = Path('/home/user/.zshrc')
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mgr.add(PROFILE, target)
        cmd = mock_run.call_args[0][0]
        assert 'add' in cmd
        assert str(target) in cmd

    def test_path_is_stringified(self) -> None:
        mgr = ChezmoiManager()
        target = Path('/some/file')
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mgr.add(PROFILE, target)
        cmd = mock_run.call_args[0][0]
        assert '/some/file' in cmd


class TestDiff:
    def test_calls_chezmoi_diff(self) -> None:
        mgr = ChezmoiManager()
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mgr.diff(PROFILE)
        cmd = mock_run.call_args[0][0]
        assert 'diff' in cmd


class TestStatus:
    def test_calls_chezmoi_status(self) -> None:
        mgr = ChezmoiManager()
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mgr.status(PROFILE)
        cmd = mock_run.call_args[0][0]
        assert 'status' in cmd


class TestListPendingPaths:
    def test_returns_existing_files_from_status_output(self, tmp_path: Path) -> None:
        target = tmp_path / '.bashrc'
        target.write_text('hello')
        status_output = f' M {target}\n'
        mgr = ChezmoiManager()
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mock_run.return_value.stdout = status_output
            result = mgr.list_pending_paths(PROFILE)
        assert target in result

    def test_skips_nonexistent_files(self, tmp_path: Path) -> None:
        missing = tmp_path / '.missing'
        status_output = f' D {missing}\n'
        mgr = ChezmoiManager()
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mock_run.return_value.stdout = status_output
            result = mgr.list_pending_paths(PROFILE)
        assert missing not in result

    def test_skips_directories(self, tmp_path: Path) -> None:
        a_dir = tmp_path / 'somedir'
        a_dir.mkdir()
        status_output = f' M {a_dir}\n'
        mgr = ChezmoiManager()
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mock_run.return_value.stdout = status_output
            result = mgr.list_pending_paths(PROFILE)
        assert a_dir not in result

    def test_empty_status_returns_empty_list(self) -> None:
        mgr = ChezmoiManager()
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mock_run.return_value.stdout = ''
            result = mgr.list_pending_paths(PROFILE)
        assert result == []

    def test_calls_chezmoi_status(self) -> None:
        mgr = ChezmoiManager()
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mock_run.return_value.stdout = ''
            mgr.list_pending_paths(PROFILE)
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == 'chezmoi'
        assert 'status' in cmd

    def test_passes_profile_flags(self) -> None:
        mgr = ChezmoiManager()
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mock_run.return_value.stdout = ''
            mgr.list_pending_paths(PROFILE)
        cmd = mock_run.call_args[0][0]
        assert f'--source={profile_source_path(PROFILE)}' in cmd

    def test_raises_when_chezmoi_missing(self) -> None:
        with (
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError),
        ):
            ChezmoiManager()

    def test_relative_path_resolved_against_home(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv('HOME', str(tmp_path))
        target = tmp_path / '.zshrc'
        target.write_text('zsh')
        status_output = ' M .zshrc\n'
        mgr = ChezmoiManager()
        with (
            patch('athome.files_managers.chezmoi.subprocess.run') as mock_run,
            patch('athome.files_managers.chezmoi.Path.home', return_value=tmp_path),
        ):
            mock_run.return_value.stdout = status_output
            result = mgr.list_pending_paths(PROFILE)
        assert target in result


class TestBackup:
    def test_returns_count_of_copied_files(self, tmp_path: Path) -> None:
        source = tmp_path / 'source.txt'
        source.write_text('hello')
        backup_dir = tmp_path / 'backup'
        mgr = ChezmoiManager()
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mock_run.return_value.stdout = f' M {source}\n'
            count = mgr.backup(PROFILE, backup_dir)
        assert count == 1

    def test_creates_backup_directory(self, tmp_path: Path) -> None:
        source = tmp_path / 'source.txt'
        source.write_text('hello')
        backup_dir = tmp_path / 'backup'
        mgr = ChezmoiManager()
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mock_run.return_value.stdout = f' M {source}\n'
            mgr.backup(PROFILE, backup_dir)
        assert backup_dir.exists()

    def test_empty_pending_returns_zero(self, tmp_path: Path) -> None:
        backup_dir = tmp_path / 'backup'
        mgr = ChezmoiManager()
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mock_run.return_value.stdout = ''
            count = mgr.backup(PROFILE, backup_dir)
        assert count == 0


class TestUnapply:
    def test_removes_file_not_in_safe_paths(self, tmp_path: Path) -> None:
        managed = tmp_path / '.bashrc'
        managed.write_text('hello')
        mgr = ChezmoiManager()
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mock_run.return_value.stdout = f'{managed}\n'
            mgr.unapply(PROFILE, frozenset())
        assert not managed.exists()

    def test_preserves_file_in_safe_paths(self, tmp_path: Path) -> None:
        managed = tmp_path / '.bashrc'
        managed.write_text('hello')
        mgr = ChezmoiManager()
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mock_run.return_value.stdout = f'{managed}\n'
            mgr.unapply(PROFILE, frozenset({managed}))
        assert managed.exists()

    def test_calls_chezmoi_managed(self) -> None:
        mgr = ChezmoiManager()
        with patch('athome.files_managers.chezmoi.subprocess.run') as mock_run:
            mock_run.return_value.stdout = ''
            mgr.unapply(PROFILE, frozenset())
        cmd = mock_run.call_args[0][0]
        assert 'managed' in cmd


class TestToolNotFound:
    def test_raises_at_instantiation_when_chezmoi_missing(self) -> None:
        with (
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError),
        ):
            ChezmoiManager()

    def test_error_message_names_tool(self) -> None:
        with (
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError) as exc_info,
        ):
            ChezmoiManager()
        assert 'chezmoi' in exc_info.value.format_message()

    def test_error_includes_install_hint(self) -> None:
        with (
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError) as exc_info,
        ):
            ChezmoiManager()
        assert 'chezmoi.io' in exc_info.value.format_message()

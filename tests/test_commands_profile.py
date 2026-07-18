"""Tests for the profile command group."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

from typer.testing import CliRunner

from athome.cli.profiles import app
from athome.definitions.config import AthomeConfig
from athome.definitions.config import ProfileConfig
from athome.profiles.orchestrator import AthomeState

runner = CliRunner()

_FULL_CFG = AthomeConfig(
    profiles={
        'work': ProfileConfig(name='work', source='https://github.com/org/dotfiles-work'),
        'personal': ProfileConfig(name='personal', source='https://github.com/user/dotfiles'),
    },
)
_EMPTY_CFG = AthomeConfig()
_EMPTY_STATE = AthomeState()


def _mock_manager(**kwargs: object) -> MagicMock:
    """Return a MagicMock with sensible defaults for SharedFileManager methods."""
    mgr = MagicMock()
    mgr.is_initialized.return_value = kwargs.get('initialized', True)
    mgr.list_pending_paths.return_value = kwargs.get('pending', [])
    mgr.backup.return_value = kwargs.get('backup_count', 0)
    return mgr


class TestInit:
    def test_unknown_profile_exits_one(self) -> None:
        with patch('athome.commands.profile.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['init', 'nope'])
        assert result.exit_code == 1

    def test_calls_manager_init_when_not_initialized(self) -> None:
        mock_mgr = _mock_manager(initialized=False)
        with (
            patch('athome.commands.profile.load_config', return_value=_FULL_CFG),
            patch('athome.commands.profile._get_manager', return_value=mock_mgr),
        ):
            result = runner.invoke(app, ['init', 'work'])
        assert result.exit_code == 0
        mock_mgr.init.assert_called_once_with(_FULL_CFG.profiles['work'])

    def test_skips_init_when_already_initialized(self) -> None:
        mock_mgr = _mock_manager(initialized=True)
        with (
            patch('athome.commands.profile.load_config', return_value=_FULL_CFG),
            patch('athome.commands.profile._get_manager', return_value=mock_mgr),
        ):
            result = runner.invoke(app, ['init', 'work'])
        assert result.exit_code == 0
        mock_mgr.init.assert_not_called()

    def test_already_initialized_message(self) -> None:
        mock_mgr = _mock_manager(initialized=True)
        with (
            patch('athome.commands.profile.load_config', return_value=_FULL_CFG),
            patch('athome.commands.profile._get_manager', return_value=mock_mgr),
        ):
            result = runner.invoke(app, ['init', 'work'])
        assert 'already initialized' in result.output

    def test_prints_next_step_hint(self) -> None:
        mock_mgr = _mock_manager(initialized=False)
        with (
            patch('athome.commands.profile.load_config', return_value=_FULL_CFG),
            patch('athome.commands.profile._get_manager', return_value=mock_mgr),
        ):
            result = runner.invoke(app, ['init', 'work'])
        assert 'apply' in result.output


class TestListProfiles:
    def test_empty_config_prints_guidance(self) -> None:
        with (
            patch('athome.commands.profile.load_config', return_value=_EMPTY_CFG),
            patch('athome.commands.profile.load_state', return_value=_EMPTY_STATE),
        ):
            result = runner.invoke(app, ['list'])
        assert result.exit_code == 0
        assert '[profiles]' in result.output

    def test_shows_each_profile_name(self) -> None:
        with (
            patch('athome.commands.profile.load_config', return_value=_FULL_CFG),
            patch('athome.commands.profile.load_state', return_value=_EMPTY_STATE),
        ):
            result = runner.invoke(app, ['list'])
        assert 'work' in result.output
        assert 'personal' in result.output

    def test_shows_source_url(self) -> None:
        with (
            patch('athome.commands.profile.load_config', return_value=_FULL_CFG),
            patch('athome.commands.profile.load_state', return_value=_EMPTY_STATE),
        ):
            result = runner.invoke(app, ['list'])
        assert 'https://github.com/org/dotfiles-work' in result.output

    def test_marks_active_profiles(self) -> None:
        active_state = AthomeState(active_profiles=['work'])
        with (
            patch('athome.commands.profile.load_config', return_value=_FULL_CFG),
            patch('athome.commands.profile.load_state', return_value=active_state),
        ):
            result = runner.invoke(app, ['list'])
        assert '*' in result.output


class TestSync:
    def test_unknown_profile_exits_one(self) -> None:
        with patch('athome.commands.profile.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['sync', 'nonexistent'])
        assert result.exit_code == 1

    def test_unknown_profile_prints_error(self) -> None:
        with patch('athome.commands.profile.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['sync', 'nonexistent'])
        assert 'nonexistent' in result.stderr
        assert '(none)' in result.stderr

    def test_known_profile_calls_manager_sync(self) -> None:
        mock_mgr = _mock_manager()
        with (
            patch('athome.commands.profile.load_config', return_value=_FULL_CFG),
            patch('athome.commands.profile._get_manager', return_value=mock_mgr),
        ):
            result = runner.invoke(app, ['sync', 'work'])
        assert result.exit_code == 0
        mock_mgr.sync.assert_called_once_with(_FULL_CFG.profiles['work'])

    def test_uninitialized_profile_exits_one(self) -> None:
        mock_mgr = _mock_manager(initialized=False)
        with (
            patch('athome.commands.profile.load_config', return_value=_FULL_CFG),
            patch('athome.commands.profile._get_manager', return_value=mock_mgr),
        ):
            result = runner.invoke(app, ['sync', 'work'])
        assert result.exit_code == 1
        assert 'init' in result.stderr

    def test_backup_flag_triggers_backup(self) -> None:
        mock_mgr = _mock_manager()
        with (
            patch('athome.commands.profile.load_config', return_value=_FULL_CFG),
            patch('athome.commands.profile._get_manager', return_value=mock_mgr),
        ):
            result = runner.invoke(app, ['sync', 'work', '--backup'])
        assert result.exit_code == 0
        mock_mgr.backup.assert_called_once()

    def test_no_backup_by_default(self) -> None:
        mock_mgr = _mock_manager()
        with (
            patch('athome.commands.profile.load_config', return_value=_FULL_CFG),
            patch('athome.commands.profile._get_manager', return_value=mock_mgr),
        ):
            runner.invoke(app, ['sync', 'work'])
        mock_mgr.backup.assert_not_called()

    def test_prints_syncing_message(self) -> None:
        mock_mgr = _mock_manager()
        with (
            patch('athome.commands.profile.load_config', return_value=_FULL_CFG),
            patch('athome.commands.profile._get_manager', return_value=mock_mgr),
        ):
            result = runner.invoke(app, ['sync', 'work'])
        assert 'work' in result.output

    def test_error_message_lists_defined_profiles(self) -> None:
        with patch('athome.commands.profile.load_config', return_value=_FULL_CFG):
            result = runner.invoke(app, ['sync', 'nope'])
        assert 'work' in result.stderr or 'personal' in result.stderr


class TestApply:
    def test_unknown_profile_exits_one(self) -> None:
        with patch('athome.commands.profile.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['apply', 'nope'])
        assert result.exit_code == 1

    def test_known_profile_calls_manager_apply(self) -> None:
        mock_mgr = _mock_manager()
        with (
            patch('athome.commands.profile.load_config', return_value=_FULL_CFG),
            patch('athome.commands.profile._get_manager', return_value=mock_mgr),
        ):
            result = runner.invoke(app, ['apply', 'work'])
        assert result.exit_code == 0
        mock_mgr.apply.assert_called_once_with(_FULL_CFG.profiles['work'])

    def test_uninitialized_profile_exits_one(self) -> None:
        mock_mgr = _mock_manager(initialized=False)
        with (
            patch('athome.commands.profile.load_config', return_value=_FULL_CFG),
            patch('athome.commands.profile._get_manager', return_value=mock_mgr),
        ):
            result = runner.invoke(app, ['apply', 'work'])
        assert result.exit_code == 1
        assert 'init' in result.stderr

    def test_backup_flag_triggers_backup(self) -> None:
        mock_mgr = _mock_manager()
        with (
            patch('athome.commands.profile.load_config', return_value=_FULL_CFG),
            patch('athome.commands.profile._get_manager', return_value=mock_mgr),
        ):
            result = runner.invoke(app, ['apply', 'work', '--backup'])
        assert result.exit_code == 0
        mock_mgr.backup.assert_called_once()

    def test_backup_name_implies_backup(self) -> None:
        mock_mgr = _mock_manager()
        with (
            patch('athome.commands.profile.load_config', return_value=_FULL_CFG),
            patch('athome.commands.profile._get_manager', return_value=mock_mgr),
        ):
            result = runner.invoke(app, ['apply', 'work', '--backup-name', 'my-snapshot'])
        assert result.exit_code == 0
        mock_mgr.backup.assert_called_once()
        backup_dir = mock_mgr.backup.call_args[0][1]
        assert 'my-snapshot' in str(backup_dir)

    def test_no_backup_by_default(self) -> None:
        mock_mgr = _mock_manager()
        with (
            patch('athome.commands.profile.load_config', return_value=_FULL_CFG),
            patch('athome.commands.profile._get_manager', return_value=mock_mgr),
        ):
            runner.invoke(app, ['apply', 'work'])
        mock_mgr.backup.assert_not_called()

    def test_backup_message_shows_path(self) -> None:
        mock_mgr = _mock_manager(backup_count=2)
        with (
            patch('athome.commands.profile.load_config', return_value=_FULL_CFG),
            patch('athome.commands.profile._get_manager', return_value=mock_mgr),
        ):
            result = runner.invoke(app, ['apply', 'work', '--backup-name', 'snap'])
        assert '2' in result.output
        assert 'snap' in result.output


class TestAdd:
    def test_unknown_profile_exits_one(self) -> None:
        with patch('athome.commands.profile.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['add', 'nope', '/some/file'])
        assert result.exit_code == 1

    def test_known_profile_calls_manager_add(self) -> None:
        mock_mgr = _mock_manager()
        with (
            patch('athome.commands.profile.load_config', return_value=_FULL_CFG),
            patch('athome.commands.profile._get_manager', return_value=mock_mgr),
        ):
            result = runner.invoke(app, ['add', 'work', '/home/user/.zshrc'])
        assert result.exit_code == 0
        mock_mgr.add.assert_called_once_with(_FULL_CFG.profiles['work'], Path('/home/user/.zshrc'))


class TestDiff:
    def test_unknown_profile_exits_one(self) -> None:
        with patch('athome.commands.profile.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['diff', 'nope'])
        assert result.exit_code == 1

    def test_known_profile_calls_manager_diff(self) -> None:
        mock_mgr = _mock_manager()
        with (
            patch('athome.commands.profile.load_config', return_value=_FULL_CFG),
            patch('athome.commands.profile._get_manager', return_value=mock_mgr),
        ):
            result = runner.invoke(app, ['diff', 'work'])
        assert result.exit_code == 0
        mock_mgr.diff.assert_called_once_with(_FULL_CFG.profiles['work'])


class TestStatus:
    def test_unknown_profile_exits_one(self) -> None:
        with patch('athome.commands.profile.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['status', 'nope'])
        assert result.exit_code == 1

    def test_known_profile_calls_manager_status(self) -> None:
        mock_mgr = _mock_manager()
        with (
            patch('athome.commands.profile.load_config', return_value=_FULL_CFG),
            patch('athome.commands.profile._get_manager', return_value=mock_mgr),
        ):
            result = runner.invoke(app, ['status', 'work'])
        assert result.exit_code == 0
        mock_mgr.status.assert_called_once_with(_FULL_CFG.profiles['work'])


class TestUnapply:
    def test_unknown_profile_exits_one(self) -> None:
        with patch('athome.commands.profile.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['unapply', 'nope'])
        assert result.exit_code == 1

    def test_calls_manager_unapply(self) -> None:
        mock_mgr = _mock_manager()
        with (
            patch('athome.commands.profile.load_config', return_value=_FULL_CFG),
            patch('athome.commands.profile._get_manager', return_value=mock_mgr),
            patch('athome.commands.profile.load_state', return_value=_EMPTY_STATE),
            patch('athome.commands.profile.save_state'),
        ):
            result = runner.invoke(app, ['unapply', 'work'])
        assert result.exit_code == 0
        mock_mgr.unapply.assert_called_once()

    def test_prints_unapply_message(self) -> None:
        mock_mgr = _mock_manager()
        with (
            patch('athome.commands.profile.load_config', return_value=_FULL_CFG),
            patch('athome.commands.profile._get_manager', return_value=mock_mgr),
            patch('athome.commands.profile.load_state', return_value=_EMPTY_STATE),
            patch('athome.commands.profile.save_state'),
        ):
            result = runner.invoke(app, ['unapply', 'work'])
        assert 'work' in result.output

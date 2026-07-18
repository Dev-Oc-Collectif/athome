"""Tests for the profile command group."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

from typer.testing import CliRunner

from athome.cli.profiles import app
from athome.definitions.config import AthomeConfig
from athome.definitions.config import ProfileConfig

runner = CliRunner()

_FULL_CFG = AthomeConfig(
    profiles={
        'work': ProfileConfig(name='work', source='https://github.com/org/dotfiles-work'),
        'personal': ProfileConfig(name='personal', source='https://github.com/user/dotfiles'),
    },
)
_EMPTY_CFG = AthomeConfig()


def _mock_manager(**kwargs: object) -> MagicMock:
    """Return a MagicMock with sensible defaults for SharedFileManager methods."""
    mgr = MagicMock()
    mgr.is_initialized.return_value = kwargs.get('initialized', True)
    return mgr


class TestAdd:
    def test_calls_config_writer_with_source(self) -> None:
        with patch('athome.cli.profiles.config_writer.add_profile') as mock_add:
            result = runner.invoke(app, ['add', 'work', 'https://github.com/org/dots'])
        assert result.exit_code == 0
        args, kwargs = mock_add.call_args
        assert args[0] == 'work'
        assert args[1] == 'https://github.com/org/dots'
        assert kwargs['destination'] is None
        assert kwargs['loads'] == []

    def test_parses_comma_separated_loads(self) -> None:
        with patch('athome.cli.profiles.config_writer.add_profile') as mock_add:
            runner.invoke(app, ['add', 'work', 'https://github.com/org/dots', '--loads', 'a, b'])
        assert mock_add.call_args.kwargs['loads'] == ['a', 'b']

    def test_destination_passed_as_string(self, tmp_path: Path) -> None:
        with patch('athome.cli.profiles.config_writer.add_profile') as mock_add:
            runner.invoke(
                app,
                ['add', 'work', 'https://github.com/org/dots', '--destination', str(tmp_path)],
            )
        assert mock_add.call_args.kwargs['destination'] == str(tmp_path)

    def test_prints_confirmation(self) -> None:
        with patch('athome.cli.profiles.config_writer.add_profile'):
            result = runner.invoke(app, ['add', 'work', 'https://github.com/org/dots'])
        assert 'work' in result.output
        assert 'init' in result.output


class TestInit:
    def test_unknown_profile_exits_one(self) -> None:
        with patch('athome.cli.profiles.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['init', 'nope'])
        assert result.exit_code == 1

    def test_calls_manager_init_when_not_initialized(self) -> None:
        mock_mgr = _mock_manager(initialized=False)
        with (
            patch('athome.cli.profiles.load_config', return_value=_FULL_CFG),
            patch('athome.cli.profiles._manager', mock_mgr),
        ):
            result = runner.invoke(app, ['init', 'work'])
        assert result.exit_code == 0
        mock_mgr.init.assert_called_once_with(_FULL_CFG.profiles['work'])

    def test_skips_init_when_already_initialized(self) -> None:
        mock_mgr = _mock_manager(initialized=True)
        with (
            patch('athome.cli.profiles.load_config', return_value=_FULL_CFG),
            patch('athome.cli.profiles._manager', mock_mgr),
        ):
            result = runner.invoke(app, ['init', 'work'])
        assert result.exit_code == 0
        mock_mgr.init.assert_not_called()

    def test_already_initialized_message(self) -> None:
        mock_mgr = _mock_manager(initialized=True)
        with (
            patch('athome.cli.profiles.load_config', return_value=_FULL_CFG),
            patch('athome.cli.profiles._manager', mock_mgr),
        ):
            result = runner.invoke(app, ['init', 'work'])
        assert 'already initialized' in result.output

    def test_prints_next_step_hint(self) -> None:
        mock_mgr = _mock_manager(initialized=False)
        with (
            patch('athome.cli.profiles.load_config', return_value=_FULL_CFG),
            patch('athome.cli.profiles._manager', mock_mgr),
        ):
            result = runner.invoke(app, ['init', 'work'])
        assert 'apply' in result.output


class TestListProfiles:
    def test_empty_config_prints_guidance(self) -> None:
        with patch('athome.cli.profiles.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['list'])
        assert result.exit_code == 0
        assert '[profiles]' in result.output

    def test_shows_each_profile_name(self) -> None:
        with patch('athome.cli.profiles.load_config', return_value=_FULL_CFG):
            result = runner.invoke(app, ['list'])
        assert 'work' in result.output
        assert 'personal' in result.output

    def test_shows_source_url(self) -> None:
        with patch('athome.cli.profiles.load_config', return_value=_FULL_CFG):
            result = runner.invoke(app, ['list'])
        assert 'https://github.com/org/dotfiles-work' in result.output


class TestSync:
    def test_unknown_profile_exits_one(self) -> None:
        with patch('athome.cli.profiles.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['sync', 'nonexistent'])
        assert result.exit_code == 1

    def test_unknown_profile_prints_error(self) -> None:
        with patch('athome.cli.profiles.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['sync', 'nonexistent'])
        assert 'nonexistent' in result.stderr
        assert '(none)' in result.stderr

    def test_known_profile_calls_manager_sync(self) -> None:
        mock_mgr = _mock_manager()
        with (
            patch('athome.cli.profiles.load_config', return_value=_FULL_CFG),
            patch('athome.cli.profiles._manager', mock_mgr),
        ):
            result = runner.invoke(app, ['sync', 'work'])
        assert result.exit_code == 0
        mock_mgr.sync.assert_called_once_with(_FULL_CFG.profiles['work'])

    def test_uninitialized_profile_exits_one(self) -> None:
        mock_mgr = _mock_manager(initialized=False)
        with (
            patch('athome.cli.profiles.load_config', return_value=_FULL_CFG),
            patch('athome.cli.profiles._manager', mock_mgr),
        ):
            result = runner.invoke(app, ['sync', 'work'])
        assert result.exit_code == 1
        assert 'init' in result.stderr

    def test_prints_syncing_message(self) -> None:
        mock_mgr = _mock_manager()
        with (
            patch('athome.cli.profiles.load_config', return_value=_FULL_CFG),
            patch('athome.cli.profiles._manager', mock_mgr),
        ):
            result = runner.invoke(app, ['sync', 'work'])
        assert 'work' in result.output

    def test_error_message_lists_defined_profiles(self) -> None:
        with patch('athome.cli.profiles.load_config', return_value=_FULL_CFG):
            result = runner.invoke(app, ['sync', 'nope'])
        assert 'work' in result.stderr or 'personal' in result.stderr


class TestApply:
    def test_unknown_profile_exits_one(self) -> None:
        with patch('athome.cli.profiles.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['apply', 'nope'])
        assert result.exit_code == 1

    def test_known_profile_calls_manager_apply(self) -> None:
        mock_mgr = _mock_manager()
        with (
            patch('athome.cli.profiles.load_config', return_value=_FULL_CFG),
            patch('athome.cli.profiles._manager', mock_mgr),
        ):
            result = runner.invoke(app, ['apply', 'work'])
        assert result.exit_code == 0
        mock_mgr.apply.assert_called_once_with(_FULL_CFG.profiles['work'])

    def test_uninitialized_profile_exits_one(self) -> None:
        mock_mgr = _mock_manager(initialized=False)
        with (
            patch('athome.cli.profiles.load_config', return_value=_FULL_CFG),
            patch('athome.cli.profiles._manager', mock_mgr),
        ):
            result = runner.invoke(app, ['apply', 'work'])
        assert result.exit_code == 1
        assert 'init' in result.stderr


class TestApplyAll:
    def test_empty_config_prints_guidance(self) -> None:
        with patch('athome.cli.profiles.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['apply-all'])
        assert result.exit_code == 0
        assert 'No profiles' in result.output

    def test_initializes_uninitialized_profiles(self) -> None:
        mock_mgr = _mock_manager(initialized=False)
        with (
            patch('athome.cli.profiles.load_config', return_value=_FULL_CFG),
            patch('athome.cli.profiles._manager', mock_mgr),
        ):
            result = runner.invoke(app, ['apply-all'])
        assert result.exit_code == 0
        assert mock_mgr.init.call_count == len(_FULL_CFG.profiles)

    def test_applies_every_profile_in_order(self) -> None:
        mock_mgr = _mock_manager()
        with (
            patch('athome.cli.profiles.load_config', return_value=_FULL_CFG),
            patch('athome.cli.profiles._manager', mock_mgr),
        ):
            runner.invoke(app, ['apply-all'])
        applied = [call.args[0].name for call in mock_mgr.apply.call_args_list]
        assert applied == list(_FULL_CFG.profiles)

    def test_skips_init_when_already_initialized(self) -> None:
        mock_mgr = _mock_manager(initialized=True)
        with (
            patch('athome.cli.profiles.load_config', return_value=_FULL_CFG),
            patch('athome.cli.profiles._manager', mock_mgr),
        ):
            runner.invoke(app, ['apply-all'])
        mock_mgr.init.assert_not_called()


class TestTrack:
    def test_unknown_profile_exits_one(self) -> None:
        with patch('athome.cli.profiles.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['track', 'nope', '/some/file'])
        assert result.exit_code == 1

    def test_known_profile_calls_manager_add(self) -> None:
        mock_mgr = _mock_manager()
        with (
            patch('athome.cli.profiles.load_config', return_value=_FULL_CFG),
            patch('athome.cli.profiles._manager', mock_mgr),
        ):
            result = runner.invoke(app, ['track', 'work', '/home/user/.zshrc'])
        assert result.exit_code == 0
        mock_mgr.add.assert_called_once_with(_FULL_CFG.profiles['work'], Path('/home/user/.zshrc'))


class TestDiff:
    def test_unknown_profile_exits_one(self) -> None:
        with patch('athome.cli.profiles.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['diff', 'nope'])
        assert result.exit_code == 1

    def test_known_profile_calls_manager_diff(self) -> None:
        mock_mgr = _mock_manager()
        with (
            patch('athome.cli.profiles.load_config', return_value=_FULL_CFG),
            patch('athome.cli.profiles._manager', mock_mgr),
        ):
            result = runner.invoke(app, ['diff', 'work'])
        assert result.exit_code == 0
        mock_mgr.diff.assert_called_once_with(_FULL_CFG.profiles['work'])


class TestStatus:
    def test_unknown_profile_exits_one(self) -> None:
        with patch('athome.cli.profiles.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['status', 'nope'])
        assert result.exit_code == 1

    def test_known_profile_calls_manager_status(self) -> None:
        mock_mgr = _mock_manager()
        with (
            patch('athome.cli.profiles.load_config', return_value=_FULL_CFG),
            patch('athome.cli.profiles._manager', mock_mgr),
        ):
            result = runner.invoke(app, ['status', 'work'])
        assert result.exit_code == 0
        mock_mgr.status.assert_called_once_with(_FULL_CFG.profiles['work'])

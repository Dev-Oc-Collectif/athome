"""Tests for the profile command group."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from athome.commands.profile import app
from athome.config import AthomeConfig
from athome.config import ProfileConfig

runner = CliRunner()

_FULL_CFG = AthomeConfig(
    profiles={
        'work': ProfileConfig(name='work', source='https://github.com/org/dotfiles-work'),
        'personal': ProfileConfig(name='personal', source='https://github.com/user/dotfiles'),
    },
)
_EMPTY_CFG = AthomeConfig()


class TestListProfiles:
    def test_empty_config_prints_guidance(self) -> None:
        with patch('athome.commands.profile.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['list'])
        assert result.exit_code == 0
        assert '[profiles]' in result.output

    def test_shows_each_profile_name(self) -> None:
        with patch('athome.commands.profile.load_config', return_value=_FULL_CFG):
            result = runner.invoke(app, ['list'])
        assert 'work' in result.output
        assert 'personal' in result.output

    def test_shows_source_url(self) -> None:
        with patch('athome.commands.profile.load_config', return_value=_FULL_CFG):
            result = runner.invoke(app, ['list'])
        assert 'https://github.com/org/dotfiles-work' in result.output


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
        with (
            patch('athome.commands.profile.load_config', return_value=_FULL_CFG),
            patch('athome.commands.profile._manager.sync') as mock_sync,
        ):
            result = runner.invoke(app, ['sync', 'work'])
        assert result.exit_code == 0
        mock_sync.assert_called_once_with(_FULL_CFG.profiles['work'])

    def test_prints_syncing_message(self) -> None:
        with (
            patch('athome.commands.profile.load_config', return_value=_FULL_CFG),
            patch('athome.commands.profile._manager.sync'),
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
        with (
            patch('athome.commands.profile.load_config', return_value=_FULL_CFG),
            patch('athome.commands.profile._manager.apply') as mock_apply,
        ):
            result = runner.invoke(app, ['apply', 'work'])
        assert result.exit_code == 0
        mock_apply.assert_called_once_with(_FULL_CFG.profiles['work'])


class TestAdd:
    def test_unknown_profile_exits_one(self) -> None:
        with patch('athome.commands.profile.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['add', 'nope', '/some/file'])
        assert result.exit_code == 1

    def test_known_profile_calls_manager_add(self) -> None:
        with (
            patch('athome.commands.profile.load_config', return_value=_FULL_CFG),
            patch('athome.commands.profile._manager.add') as mock_add,
        ):
            result = runner.invoke(app, ['add', 'work', '/home/user/.zshrc'])
        assert result.exit_code == 0
        mock_add.assert_called_once_with(_FULL_CFG.profiles['work'], Path('/home/user/.zshrc'))


class TestDiff:
    def test_unknown_profile_exits_one(self) -> None:
        with patch('athome.commands.profile.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['diff', 'nope'])
        assert result.exit_code == 1

    def test_known_profile_calls_manager_diff(self) -> None:
        with (
            patch('athome.commands.profile.load_config', return_value=_FULL_CFG),
            patch('athome.commands.profile._manager.diff') as mock_diff,
        ):
            result = runner.invoke(app, ['diff', 'work'])
        assert result.exit_code == 0
        mock_diff.assert_called_once_with(_FULL_CFG.profiles['work'])


class TestStatus:
    def test_unknown_profile_exits_one(self) -> None:
        with patch('athome.commands.profile.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['status', 'nope'])
        assert result.exit_code == 1

    def test_known_profile_calls_manager_status(self) -> None:
        with (
            patch('athome.commands.profile.load_config', return_value=_FULL_CFG),
            patch('athome.commands.profile._manager.status') as mock_status,
        ):
            result = runner.invoke(app, ['status', 'work'])
        assert result.exit_code == 0
        mock_status.assert_called_once_with(_FULL_CFG.profiles['work'])

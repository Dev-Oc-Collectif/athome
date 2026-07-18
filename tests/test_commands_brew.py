"""Tests for the brew command group."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from athome.cli.brew import app
from athome.definitions.config import AthomeConfig
from athome.definitions.config import BrewEntryConfig

runner = CliRunner()

_CFG = AthomeConfig(
    brew={
        'work': BrewEntryConfig(manifest=Path('/home/user/.config/brew/work.Brewfile')),
        'personal': BrewEntryConfig(manifest=Path('/home/user/.config/brew/personal.Brewfile')),
    },
)
_EMPTY_CFG = AthomeConfig()


class TestBrewSync:
    def test_no_entries_exits_one(self) -> None:
        with patch('athome.cli.brew.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['sync'])
        assert result.exit_code == 1

    def test_unknown_entry_exits_one(self) -> None:
        with patch('athome.cli.brew.load_config', return_value=_CFG):
            result = runner.invoke(app, ['sync', 'nope'])
        assert result.exit_code == 1

    def test_syncs_named_entry(self) -> None:
        with (
            patch('athome.cli.brew.load_config', return_value=_CFG),
            patch('athome.cli.brew._manager.sync') as mock_sync,
        ):
            result = runner.invoke(app, ['sync', 'work'])
        assert result.exit_code == 0
        mock_sync.assert_called_once_with(_CFG.brew['work'].manifest)

    def test_syncs_all_entries_when_name_omitted(self) -> None:
        with (
            patch('athome.cli.brew.load_config', return_value=_CFG),
            patch('athome.cli.brew._manager.sync') as mock_sync,
        ):
            runner.invoke(app, ['sync'])
        assert mock_sync.call_count == len(_CFG.brew)


class TestBrewUpgrade:
    def test_no_entries_exits_one(self) -> None:
        with patch('athome.cli.brew.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['upgrade'])
        assert result.exit_code == 1

    def test_unknown_entry_exits_one(self) -> None:
        with patch('athome.cli.brew.load_config', return_value=_CFG):
            result = runner.invoke(app, ['upgrade', 'nope'])
        assert result.exit_code == 1

    def test_upgrades_named_entry(self) -> None:
        with (
            patch('athome.cli.brew.load_config', return_value=_CFG),
            patch('athome.cli.brew._manager.upgrade') as mock_upgrade,
        ):
            result = runner.invoke(app, ['upgrade', 'work'])
        assert result.exit_code == 0
        mock_upgrade.assert_called_once_with(None)

    def test_passes_tool_flag(self) -> None:
        with (
            patch('athome.cli.brew.load_config', return_value=_CFG),
            patch('athome.cli.brew._manager.upgrade') as mock_upgrade,
        ):
            runner.invoke(app, ['upgrade', 'work', '--tool', 'git'])
        mock_upgrade.assert_called_once_with('git')


class TestBrewList:
    def test_no_entries_prints_guidance(self) -> None:
        with patch('athome.cli.brew.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['list'])
        assert result.exit_code == 0
        assert '[brew]' in result.output

    def test_lists_all_entries_when_name_omitted(self) -> None:
        with patch('athome.cli.brew.load_config', return_value=_CFG):
            result = runner.invoke(app, ['list'])
        assert 'work' in result.output
        assert 'personal' in result.output

    def test_unknown_entry_exits_one(self) -> None:
        with patch('athome.cli.brew.load_config', return_value=_CFG):
            result = runner.invoke(app, ['list', 'nope'])
        assert result.exit_code == 1

    def test_known_entry_calls_list_tools(self) -> None:
        with (
            patch('athome.cli.brew.load_config', return_value=_CFG),
            patch('athome.cli.brew._manager.list_tools') as mock_list,
        ):
            result = runner.invoke(app, ['list', 'work'])
        assert result.exit_code == 0
        mock_list.assert_called_once()


class TestBrewAdd:
    def test_calls_config_writer(self, tmp_path: Path) -> None:
        manifest = tmp_path / 'Brewfile'
        with patch('athome.cli.brew.config_writer.add_brew_entry') as mock_add:
            result = runner.invoke(app, ['add', 'work', str(manifest)])
        assert result.exit_code == 0
        args = mock_add.call_args.args
        assert args[0] == 'work'
        assert args[1] == str(manifest)

    def test_prints_confirmation(self, tmp_path: Path) -> None:
        manifest = tmp_path / 'Brewfile'
        with patch('athome.cli.brew.config_writer.add_brew_entry'):
            result = runner.invoke(app, ['add', 'work', str(manifest)])
        assert 'work' in result.output

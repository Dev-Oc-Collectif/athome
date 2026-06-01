"""Tests for the workspace command group."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

from typer.testing import CliRunner

from athome.commands.workspace import app
from athome.config import AthomeConfig
from athome.config import GitConfig

runner = CliRunner()

_CFG_WITH_OWNERS = AthomeConfig(
    git=GitConfig(
        owners={'gh': {'org': 'https://github.com/my-org'}},
        repositories={'gh': {'dotfiles': 'https://github.com/user/dotfiles'}},
    )
)
_EMPTY_CFG = AthomeConfig()


class TestWorkspaceSync:
    def test_no_owners_exits_one(self, tmp_path: Path) -> None:
        with patch('athome.commands.workspace.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['sync', '--dest', str(tmp_path)])
        assert result.exit_code == 1

    def test_no_owners_prints_guidance(self, tmp_path: Path) -> None:
        with patch('athome.commands.workspace.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['sync', '--dest', str(tmp_path)])
        assert 'git.owners' in result.stderr

    def test_calls_sync_workspace_for_each_owner(self, tmp_path: Path) -> None:
        mock_gh = MagicMock()
        with (
            patch('athome.commands.workspace.load_config', return_value=_CFG_WITH_OWNERS),
            patch.dict('athome.commands.workspace._MANAGERS', {'gh': mock_gh}),
        ):
            result = runner.invoke(app, ['sync', '--dest', str(tmp_path)])
        assert result.exit_code == 0
        mock_gh.sync_workspace.assert_called_once_with(
            'https://github.com/my-org',
            tmp_path / 'gh' / 'org',
        )

    def test_calls_clone_for_each_individual_repo(self, tmp_path: Path) -> None:
        mock_gh = MagicMock()
        with (
            patch('athome.commands.workspace.load_config', return_value=_CFG_WITH_OWNERS),
            patch.dict('athome.commands.workspace._MANAGERS', {'gh': mock_gh}),
        ):
            result = runner.invoke(app, ['sync', '--dest', str(tmp_path)])
        assert result.exit_code == 0
        mock_gh.clone.assert_called_once_with(
            'https://github.com/user/dotfiles',
            tmp_path / 'gh' / 'dotfiles',
        )

    def test_prints_syncing_message(self, tmp_path: Path) -> None:
        mock_gh = MagicMock()
        with (
            patch('athome.commands.workspace.load_config', return_value=_CFG_WITH_OWNERS),
            patch.dict('athome.commands.workspace._MANAGERS', {'gh': mock_gh}),
        ):
            result = runner.invoke(app, ['sync', '--dest', str(tmp_path)])
        assert 'gh/org' in result.output

    def test_short_dest_option(self, tmp_path: Path) -> None:
        mock_gh = MagicMock()
        with (
            patch('athome.commands.workspace.load_config', return_value=_CFG_WITH_OWNERS),
            patch.dict('athome.commands.workspace._MANAGERS', {'gh': mock_gh}),
        ):
            result = runner.invoke(app, ['sync', '-d', str(tmp_path)])
        assert result.exit_code == 0

    def test_unknown_provider_skips_with_warning(self, tmp_path: Path) -> None:
        cfg = AthomeConfig(git=GitConfig(owners={'unknown': {'org': 'https://some-git/org'}}))
        with patch('athome.commands.workspace.load_config', return_value=cfg):
            result = runner.invoke(app, ['sync', '--dest', str(tmp_path)])
        assert 'unknown' in result.stderr

    def test_uses_git_workspace_from_config_as_default_dest(self) -> None:
        custom = Path('/custom/workspace')
        cfg = AthomeConfig(
            git=GitConfig(
                workspace=custom,
                owners={'gh': {'org': 'https://github.com/my-org'}},
            )
        )
        mock_gh = MagicMock()
        with (
            patch('athome.commands.workspace.load_config', return_value=cfg),
            patch.dict('athome.commands.workspace._MANAGERS', {'gh': mock_gh}),
        ):
            result = runner.invoke(app, ['sync'])
        assert result.exit_code == 0
        mock_gh.sync_workspace.assert_called_once_with(
            'https://github.com/my-org',
            custom / 'gh' / 'org',
        )


class TestWorkspaceList:
    def test_no_provider_lists_configured_providers(self) -> None:
        with patch('athome.commands.workspace.load_config', return_value=_CFG_WITH_OWNERS):
            result = runner.invoke(app, ['list'])
        assert 'gh' in result.output
        assert result.exit_code == 0

    def test_no_provider_empty_config_exits_one(self) -> None:
        with patch('athome.commands.workspace.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['list'])
        assert result.exit_code == 1

    def test_no_provider_empty_config_prints_error(self) -> None:
        with patch('athome.commands.workspace.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['list'])
        assert 'configured' in result.stderr

    def test_known_provider_calls_list_repos_without_owner(self) -> None:
        mock_gh = MagicMock()
        with patch.dict('athome.commands.workspace._MANAGERS', {'gh': mock_gh}):
            runner.invoke(app, ['list', 'gh'])
        mock_gh.list_repos.assert_called_once_with(None)

    def test_known_provider_with_owner_passes_owner(self) -> None:
        mock_gh = MagicMock()
        with patch.dict('athome.commands.workspace._MANAGERS', {'gh': mock_gh}):
            runner.invoke(app, ['list', 'gh', '--owner', 'my-org'])
        mock_gh.list_repos.assert_called_once_with('my-org')

    def test_unknown_provider_exits_one(self) -> None:
        result = runner.invoke(app, ['list', 'unknown'])
        assert result.exit_code == 1

    def test_unknown_provider_prints_error(self) -> None:
        result = runner.invoke(app, ['list', 'unknown'])
        assert 'unknown' in result.stderr

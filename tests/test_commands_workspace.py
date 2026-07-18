"""Tests for the workspace command group."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

from typer.testing import CliRunner

from athome.cli.workspaces import app
from athome.definitions.config import AthomeConfig
from athome.definitions.config import DestinationConfig
from athome.definitions.config import OwnerConfig
from athome.definitions.config import RepoConfig
from athome.definitions.config import WorkspaceConfig

runner = CliRunner()

_CFG_WITH_OWNERS = AthomeConfig(
    workspace=WorkspaceConfig(
        owners={'my-org': OwnerConfig(source='https://github.com/my-org', manager='gh')},
        repos={'dotfiles': RepoConfig(source='https://github.com/user/dotfiles', manager='gh')},
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
        assert 'workspace.owners' in result.stderr

    def test_calls_sync_for_each_owner(self, tmp_path: Path) -> None:
        mock_gh = MagicMock()
        with (
            patch('athome.commands.workspace.load_config', return_value=_CFG_WITH_OWNERS),
            patch(
                'athome.commands.workspace._registry.all',
                return_value={'gh': mock_gh},
            ),
        ):
            result = runner.invoke(app, ['sync', '--dest', str(tmp_path)])
        assert result.exit_code == 0
        mock_gh.sync.assert_called_once_with(
            'https://github.com/my-org',
            tmp_path / 'my-org',
        )

    def test_calls_clone_for_each_individual_repo(self, tmp_path: Path) -> None:
        mock_gh = MagicMock()
        with (
            patch('athome.commands.workspace.load_config', return_value=_CFG_WITH_OWNERS),
            patch(
                'athome.commands.workspace._registry.all',
                return_value={'gh': mock_gh},
            ),
        ):
            result = runner.invoke(app, ['sync', '--dest', str(tmp_path)])
        assert result.exit_code == 0
        mock_gh.clone.assert_called_once_with(
            'https://github.com/user/dotfiles',
            tmp_path / 'dotfiles',
        )

    def test_prints_syncing_message(self, tmp_path: Path) -> None:
        mock_gh = MagicMock()
        with (
            patch('athome.commands.workspace.load_config', return_value=_CFG_WITH_OWNERS),
            patch(
                'athome.commands.workspace._registry.all',
                return_value={'gh': mock_gh},
            ),
        ):
            result = runner.invoke(app, ['sync', '--dest', str(tmp_path)])
        assert 'my-org' in result.output

    def test_short_dest_option(self, tmp_path: Path) -> None:
        mock_gh = MagicMock()
        with (
            patch('athome.commands.workspace.load_config', return_value=_CFG_WITH_OWNERS),
            patch(
                'athome.commands.workspace._registry.all',
                return_value={'gh': mock_gh},
            ),
        ):
            result = runner.invoke(app, ['sync', '-d', str(tmp_path)])
        assert result.exit_code == 0

    def test_unknown_manager_skips_with_warning(self, tmp_path: Path) -> None:
        cfg = AthomeConfig(
            workspace=WorkspaceConfig(
                owners={'work': OwnerConfig(source='https://some-git/org', manager='unknown')}
            )
        )
        with (
            patch('athome.commands.workspace.load_config', return_value=cfg),
            patch('athome.commands.workspace._registry.all', return_value={}),
        ):
            result = runner.invoke(app, ['sync', '--dest', str(tmp_path)])
        assert 'unknown' in result.stderr

    def test_uses_workspace_destination_from_config_as_default_dest(self) -> None:
        custom = Path('/custom/workspace')
        cfg = AthomeConfig(
            workspace=WorkspaceConfig(
                destination=DestinationConfig(target=custom),
                owners={'my-org': OwnerConfig(source='https://github.com/my-org', manager='gh')},
            )
        )
        mock_gh = MagicMock()
        with (
            patch('athome.commands.workspace.load_config', return_value=cfg),
            patch(
                'athome.commands.workspace._registry.all',
                return_value={'gh': mock_gh},
            ),
        ):
            result = runner.invoke(app, ['sync'])
        assert result.exit_code == 0
        mock_gh.sync.assert_called_once_with(
            'https://github.com/my-org',
            custom / 'my-org',
        )


class TestWorkspaceList:
    def test_no_owner_lists_configured_owners(self) -> None:
        with patch('athome.commands.workspace.load_config', return_value=_CFG_WITH_OWNERS):
            result = runner.invoke(app, ['list'])
        assert 'my-org' in result.output
        assert result.exit_code == 0

    def test_list_shows_manager(self) -> None:
        with patch('athome.commands.workspace.load_config', return_value=_CFG_WITH_OWNERS):
            result = runner.invoke(app, ['list'])
        assert 'gh' in result.output

    def test_no_owner_empty_config_exits_one(self) -> None:
        with patch('athome.commands.workspace.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['list'])
        assert result.exit_code == 1

    def test_no_owner_empty_config_prints_error(self) -> None:
        with patch('athome.commands.workspace.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['list'])
        assert 'configured' in result.stderr

    def test_known_owner_calls_list_repos(self) -> None:
        mock_gh = MagicMock()
        with (
            patch('athome.commands.workspace.load_config', return_value=_CFG_WITH_OWNERS),
            patch(
                'athome.commands.workspace._registry.all',
                return_value={'gh': mock_gh},
            ),
        ):
            runner.invoke(app, ['list', 'my-org'])
        mock_gh.list_repos.assert_called_once_with(None)

    def test_unknown_owner_exits_one(self) -> None:
        with (
            patch('athome.commands.workspace.load_config', return_value=_CFG_WITH_OWNERS),
            patch('athome.commands.workspace._registry.all', return_value={}),
        ):
            result = runner.invoke(app, ['list', 'unknown'])
        assert result.exit_code == 1

    def test_unknown_owner_prints_error(self) -> None:
        with (
            patch('athome.commands.workspace.load_config', return_value=_CFG_WITH_OWNERS),
            patch('athome.commands.workspace._registry.all', return_value={}),
        ):
            result = runner.invoke(app, ['list', 'unknown'])
        assert 'unknown' in result.stderr

"""Tests for the repo command group (ad hoc gh commands + config-driven sync)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from athome.cli.repo import app
from athome.definitions.config import AthomeConfig
from athome.definitions.config import DestinationConfig
from athome.definitions.config import OwnerConfig
from athome.definitions.config import RepoConfig
from athome.definitions.config import WorkspaceConfig

runner = CliRunner()

_CFG_WITH_OWNERS = AthomeConfig(
    workspace=WorkspaceConfig(
        owners={'my-org': OwnerConfig(source='https://github.com/my-org')},
        repos={'dotfiles': RepoConfig(source='https://github.com/user/dotfiles')},
    )
)
_EMPTY_CFG = AthomeConfig()


class TestAddOwner:
    def test_calls_config_writer(self) -> None:
        with patch('athome.cli.repo.config_writer.add_owner') as mock_add:
            result = runner.invoke(app, ['add-owner', 'myorg', 'https://github.com/myorg'])
        assert result.exit_code == 0
        mock_add.assert_called_once()
        args = mock_add.call_args.args
        assert args[0] == 'myorg'
        assert args[1] == 'https://github.com/myorg'

    def test_prints_confirmation(self) -> None:
        with patch('athome.cli.repo.config_writer.add_owner'):
            result = runner.invoke(app, ['add-owner', 'myorg', 'https://github.com/myorg'])
        assert 'myorg' in result.output


class TestAddRepo:
    def test_calls_config_writer(self) -> None:
        with patch('athome.cli.repo.config_writer.add_repo') as mock_add:
            result = runner.invoke(
                app, ['add-repo', 'dotfiles', 'https://github.com/user/dotfiles']
            )
        assert result.exit_code == 0
        mock_add.assert_called_once()
        args = mock_add.call_args.args
        assert args[0] == 'dotfiles'
        assert args[1] == 'https://github.com/user/dotfiles'

    def test_prints_confirmation(self) -> None:
        with patch('athome.cli.repo.config_writer.add_repo'):
            result = runner.invoke(
                app, ['add-repo', 'dotfiles', 'https://github.com/user/dotfiles']
            )
        assert 'dotfiles' in result.output


class TestRepoCreate:
    def test_creates_private_repo_by_default(self) -> None:
        with patch('athome.cli.repo._manager.create_repo') as mock_create:
            result = runner.invoke(app, ['create', 'my-repo'])
        assert result.exit_code == 0
        mock_create.assert_called_once_with('my-repo', private=True)

    def test_creates_public_repo_with_flag(self) -> None:
        with patch('athome.cli.repo._manager.create_repo') as mock_create:
            result = runner.invoke(app, ['create', 'my-repo', '--public'])
        assert result.exit_code == 0
        mock_create.assert_called_once_with('my-repo', private=False)

    def test_prints_creating_message(self) -> None:
        with patch('athome.cli.repo._manager.create_repo'):
            result = runner.invoke(app, ['create', 'my-repo'])
        assert 'my-repo' in result.output
        assert 'private' in result.output

    def test_public_flag_shown_in_message(self) -> None:
        with patch('athome.cli.repo._manager.create_repo'):
            result = runner.invoke(app, ['create', 'my-repo', '--public'])
        assert 'public' in result.output


class TestRepoClone:
    def test_without_destination(self) -> None:
        with patch('athome.cli.repo._manager.clone') as mock_clone:
            result = runner.invoke(app, ['clone', 'org/repo'])
        assert result.exit_code == 0
        mock_clone.assert_called_once_with('org/repo', None)

    def test_with_destination(self, tmp_path: Path) -> None:
        with patch('athome.cli.repo._manager.clone') as mock_clone:
            result = runner.invoke(app, ['clone', 'org/repo', str(tmp_path)])
        assert result.exit_code == 0
        mock_clone.assert_called_once_with('org/repo', tmp_path)


class TestRepoList:
    def test_without_owner_passes_none(self) -> None:
        with patch('athome.cli.repo._manager.list_repos') as mock_list:
            result = runner.invoke(app, ['list'])
        assert result.exit_code == 0
        mock_list.assert_called_once_with(None)

    def test_with_owner_passes_owner(self) -> None:
        with patch('athome.cli.repo._manager.list_repos') as mock_list:
            result = runner.invoke(app, ['list', 'my-org'])
        assert result.exit_code == 0
        mock_list.assert_called_once_with('my-org')


class TestRepoSync:
    def test_no_owners_or_repos_exits_one(self, tmp_path: Path) -> None:
        with patch('athome.cli.repo.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['sync', '--dest', str(tmp_path)])
        assert result.exit_code == 1

    def test_no_owners_or_repos_prints_guidance(self, tmp_path: Path) -> None:
        with patch('athome.cli.repo.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['sync', '--dest', str(tmp_path)])
        assert 'workspace.owners' in result.stderr

    def test_calls_sync_for_each_owner(self, tmp_path: Path) -> None:
        with (
            patch('athome.cli.repo.load_config', return_value=_CFG_WITH_OWNERS),
            patch('athome.cli.repo._manager.sync') as mock_sync,
            patch('athome.cli.repo._manager.clone'),
        ):
            result = runner.invoke(app, ['sync', '--dest', str(tmp_path)])
        assert result.exit_code == 0
        mock_sync.assert_called_once_with(
            'https://github.com/my-org',
            tmp_path / 'my-org',
        )

    def test_calls_clone_for_each_individual_repo(self, tmp_path: Path) -> None:
        with (
            patch('athome.cli.repo.load_config', return_value=_CFG_WITH_OWNERS),
            patch('athome.cli.repo._manager.sync'),
            patch('athome.cli.repo._manager.clone') as mock_clone,
        ):
            result = runner.invoke(app, ['sync', '--dest', str(tmp_path)])
        assert result.exit_code == 0
        mock_clone.assert_called_once_with(
            'https://github.com/user/dotfiles',
            tmp_path / 'dotfiles',
        )

    def test_prints_syncing_message(self, tmp_path: Path) -> None:
        with (
            patch('athome.cli.repo.load_config', return_value=_CFG_WITH_OWNERS),
            patch('athome.cli.repo._manager.sync'),
            patch('athome.cli.repo._manager.clone'),
        ):
            result = runner.invoke(app, ['sync', '--dest', str(tmp_path)])
        assert 'my-org' in result.output

    def test_short_dest_option(self, tmp_path: Path) -> None:
        with (
            patch('athome.cli.repo.load_config', return_value=_CFG_WITH_OWNERS),
            patch('athome.cli.repo._manager.sync'),
            patch('athome.cli.repo._manager.clone'),
        ):
            result = runner.invoke(app, ['sync', '-d', str(tmp_path)])
        assert result.exit_code == 0

    def test_uses_workspace_destination_from_config_as_default_dest(self) -> None:
        custom = Path('/custom/workspace')
        cfg = AthomeConfig(
            workspace=WorkspaceConfig(
                destination=DestinationConfig(target=custom),
                owners={'my-org': OwnerConfig(source='https://github.com/my-org')},
            )
        )
        with (
            patch('athome.cli.repo.load_config', return_value=cfg),
            patch('athome.cli.repo._manager.sync') as mock_sync,
        ):
            result = runner.invoke(app, ['sync'])
        assert result.exit_code == 0
        mock_sync.assert_called_once_with(
            'https://github.com/my-org',
            custom / 'my-org',
        )

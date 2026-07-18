"""Tests for the repo command group."""

from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from athome.cli.repo import app

runner = CliRunner()


class TestRepoCreate:
    def test_creates_private_repo_by_default(self) -> None:
        with patch('athome.commands.repo._manager.create_repo') as mock_create:
            result = runner.invoke(app, ['create', 'my-repo'])
        assert result.exit_code == 0
        mock_create.assert_called_once_with('my-repo', private=True)

    def test_creates_public_repo_with_flag(self) -> None:
        with patch('athome.commands.repo._manager.create_repo') as mock_create:
            result = runner.invoke(app, ['create', 'my-repo', '--public'])
        assert result.exit_code == 0
        mock_create.assert_called_once_with('my-repo', private=False)

    def test_prints_creating_message(self) -> None:
        with patch('athome.commands.repo._manager.create_repo'):
            result = runner.invoke(app, ['create', 'my-repo'])
        assert 'my-repo' in result.output
        assert 'private' in result.output

    def test_public_flag_shown_in_message(self) -> None:
        with patch('athome.commands.repo._manager.create_repo'):
            result = runner.invoke(app, ['create', 'my-repo', '--public'])
        assert 'public' in result.output


class TestRepoList:
    def test_without_owner_passes_none(self) -> None:
        with patch('athome.commands.repo._manager.list_repos') as mock_list:
            result = runner.invoke(app, ['list'])
        assert result.exit_code == 0
        mock_list.assert_called_once_with(None)

    def test_with_owner_passes_owner(self) -> None:
        with patch('athome.commands.repo._manager.list_repos') as mock_list:
            result = runner.invoke(app, ['list', 'my-org'])
        assert result.exit_code == 0
        mock_list.assert_called_once_with('my-org')

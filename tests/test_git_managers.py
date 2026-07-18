"""Tests for GhManager — GitManager backed by the gh CLI."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from athome.definitions.managers.workspace import WorkspaceManager
from athome.exceptions import ToolNotFoundError
from athome.workspaces.managers.gh import GhManager

_BASE_PATCH = 'athome.interfaces.base.shutil.which'


@pytest.fixture(autouse=True)
def git_tools_available() -> Generator[None]:  # type: ignore[return]
    def _which(tool: str) -> str:
        return f'/usr/bin/{tool}'

    with patch(_BASE_PATCH, side_effect=_which):
        yield


class TestGhManagerContract:
    def test_is_git_manager(self) -> None:
        assert issubclass(GhManager, WorkspaceManager)

    def test_instantiates(self) -> None:
        assert isinstance(GhManager(), GhManager)


class TestListRepos:
    def test_without_owner(self) -> None:
        mgr = GhManager()
        with patch('athome.git_managers.gh.subprocess.run') as mock_run:
            mgr.list_repos()
        cmd = mock_run.call_args[0][0]
        assert cmd == ['gh', 'repo', 'list']

    def test_with_owner_appends_it(self) -> None:
        mgr = GhManager()
        with patch('athome.git_managers.gh.subprocess.run') as mock_run:
            mgr.list_repos('my-org')
        cmd = mock_run.call_args[0][0]
        assert cmd == ['gh', 'repo', 'list', 'my-org']

    def test_check_is_true(self) -> None:
        mgr = GhManager()
        with patch('athome.git_managers.gh.subprocess.run') as mock_run:
            mgr.list_repos()
        assert mock_run.call_args[1].get('check') is True


class TestClone:
    def test_without_destination(self) -> None:
        mgr = GhManager()
        with patch('athome.git_managers.gh.subprocess.run') as mock_run:
            mgr.clone('https://github.com/org/repo')
        cmd = mock_run.call_args[0][0]
        assert cmd == ['gh', 'repo', 'clone', 'https://github.com/org/repo']

    def test_with_destination_appended(self) -> None:
        mgr = GhManager()
        dest = Path('/workspace/repo')
        with patch('athome.git_managers.gh.subprocess.run') as mock_run:
            mgr.clone('https://github.com/org/repo', dest)
        cmd = mock_run.call_args[0][0]
        assert str(dest) in cmd

    def test_destination_is_stringified(self) -> None:
        mgr = GhManager()
        dest = Path('/workspace/my-project')
        with patch('athome.git_managers.gh.subprocess.run') as mock_run:
            mgr.clone('https://github.com/org/repo', dest)
        cmd = mock_run.call_args[0][0]
        assert '/workspace/my-project' in cmd


class TestSync:
    def test_creates_destination_directory(self, tmp_path: Path) -> None:
        mgr = GhManager()
        dest = tmp_path / 'workspace'
        with patch('athome.git_managers.gh.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout='')
            mgr.sync('https://github.com/org', dest)
        assert dest.exists()

    def test_clones_new_repo(self, tmp_path: Path) -> None:
        mgr = GhManager()
        dest = tmp_path / 'ws'
        owner_name = 'org'
        repo_name = 'myrepo'

        with patch('athome.git_managers.gh.subprocess.run') as mock_run:
            mock_run.side_effect = [
                MagicMock(stdout=f'{repo_name}\n'),  # gh repo list
                None,  # git clone
            ]
            mgr.sync(owner_name, dest)

        clone_call = mock_run.call_args_list[1]
        cmd = clone_call[0][0]
        assert cmd[0] == 'gh'
        assert 'clone' in cmd
        assert f'{owner_name}/{repo_name}' in cmd

    def test_pulls_existing_repo(self, tmp_path: Path) -> None:
        mgr = GhManager()
        dest = tmp_path / 'ws'
        owner_name = 'org'
        repo_name = 'myrepo'
        repo_dir = dest / owner_name / repo_name
        repo_dir.mkdir(parents=True)

        with patch('athome.git_managers.gh.subprocess.run') as mock_run:
            mock_run.side_effect = [
                MagicMock(stdout=f'{repo_name}\n'),  # gh repo list
                None,  # git pull
            ]
            mgr.sync(owner_name, dest)

        pull_call = mock_run.call_args_list[1]
        cmd = pull_call[0][0]
        assert 'sync' in cmd
        assert f'{owner_name}/{repo_name}' in cmd

    def test_empty_repo_list_makes_no_git_calls(self, tmp_path: Path) -> None:
        mgr = GhManager()
        dest = tmp_path / 'ws'

        with patch('athome.git_managers.gh.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout='')
            mgr.sync('https://github.com/org', dest)

        assert mock_run.call_count == 1  # only the gh repo list call

    def test_repo_name_stripped_of_git_suffix(self, tmp_path: Path) -> None:
        mgr = GhManager()
        dest = tmp_path / 'ws'
        owner_name = 'org'
        repo_name = 'myrepo'

        with patch('athome.git_managers.gh.subprocess.run') as mock_run:
            mock_run.side_effect = [
                MagicMock(stdout=f'{repo_name}\n'),
                None,
            ]
            mgr.sync(owner_name, dest)

        clone_call = mock_run.call_args_list[1]
        cmd = clone_call[0][0]
        expected_path = f'{owner_name}/{repo_name}'
        assert expected_path in cmd


class TestCreateRepo:
    def test_creates_private_by_default(self) -> None:
        mgr = GhManager()
        with patch('athome.git_managers.gh.subprocess.run') as mock_run:
            mgr.create_repo('my-repo')
        cmd = mock_run.call_args[0][0]
        assert '--private' in cmd
        assert 'my-repo' in cmd

    def test_creates_public_when_requested(self) -> None:
        mgr = GhManager()
        with patch('athome.git_managers.gh.subprocess.run') as mock_run:
            mgr.create_repo('my-repo', private=False)
        cmd = mock_run.call_args[0][0]
        assert '--public' in cmd

    def test_uses_gh_repo_create(self) -> None:
        mgr = GhManager()
        with patch('athome.git_managers.gh.subprocess.run') as mock_run:
            mgr.create_repo('my-repo')
        cmd = mock_run.call_args[0][0]
        assert cmd[:3] == ['gh', 'repo', 'create']


class TestToolNotFound:
    def test_raises_at_instantiation_when_gh_missing(self) -> None:
        with (
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError),
        ):
            GhManager()

    def test_error_names_gh(self) -> None:
        with (
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError) as exc_info,
        ):
            GhManager()
        assert 'gh' in exc_info.value.format_message()

    def test_error_includes_install_hint(self) -> None:
        with (
            patch(_BASE_PATCH, return_value=None),
            pytest.raises(ToolNotFoundError) as exc_info,
        ):
            GhManager()
        assert 'cli.github.com' in exc_info.value.format_message()

"""Tests for GhManager — GitManager backed by the gh CLI."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from athome.exceptions import ToolNotFoundError
from athome.git_managers.gh import GhManager
from athome.interfaces.git_manager import GitManager


@pytest.fixture(autouse=True)
def git_tools_available() -> Generator[None]:
    def _which(tool: str) -> str:
        return f'/usr/bin/{tool}'

    with patch('athome.git_managers.gh.shutil.which', side_effect=_which):
        yield


class TestGhManagerContract:
    def test_is_git_manager(self) -> None:
        assert issubclass(GhManager, GitManager)

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


class TestSyncWorkspace:
    def test_creates_destination_directory(self, tmp_path: Path) -> None:
        mgr = GhManager()
        dest = tmp_path / 'workspace'
        with patch('athome.git_managers.gh.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout='')
            mgr.sync_workspace('https://github.com/org', dest)
        assert dest.exists()

    def test_clones_new_repo(self, tmp_path: Path) -> None:
        mgr = GhManager()
        dest = tmp_path / 'ws'
        repo_url = 'git@github.com:org/myrepo.git'

        with patch('athome.git_managers.gh.subprocess.run') as mock_run:
            mock_run.side_effect = [
                MagicMock(stdout=f'{repo_url}\n'),  # gh repo list
                None,  # git clone
            ]
            mgr.sync_workspace('https://github.com/org', dest)

        clone_call = mock_run.call_args_list[1]
        cmd = clone_call[0][0]
        assert cmd[0] == 'git'
        assert 'clone' in cmd
        assert repo_url in cmd

    def test_pulls_existing_repo(self, tmp_path: Path) -> None:
        mgr = GhManager()
        dest = tmp_path / 'ws'
        repo_url = 'git@github.com:org/myrepo.git'
        repo_dir = dest / 'myrepo'
        repo_dir.mkdir(parents=True)

        with patch('athome.git_managers.gh.subprocess.run') as mock_run:
            mock_run.side_effect = [
                MagicMock(stdout=f'{repo_url}\n'),  # gh repo list
                None,  # git pull
            ]
            mgr.sync_workspace('https://github.com/org', dest)

        pull_call = mock_run.call_args_list[1]
        cmd = pull_call[0][0]
        assert 'pull' in cmd
        assert '--ff-only' in cmd

    def test_empty_repo_list_makes_no_git_calls(self, tmp_path: Path) -> None:
        mgr = GhManager()
        dest = tmp_path / 'ws'

        with patch('athome.git_managers.gh.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout='')
            mgr.sync_workspace('https://github.com/org', dest)

        assert mock_run.call_count == 1  # only the gh repo list call

    def test_repo_name_stripped_of_git_suffix(self, tmp_path: Path) -> None:
        mgr = GhManager()
        dest = tmp_path / 'ws'
        repo_url = 'git@github.com:org/myproject.git'

        with patch('athome.git_managers.gh.subprocess.run') as mock_run:
            mock_run.side_effect = [
                MagicMock(stdout=f'{repo_url}\n'),
                None,
            ]
            mgr.sync_workspace('https://github.com/org', dest)

        clone_call = mock_run.call_args_list[1]
        cmd = clone_call[0][0]
        expected_path = str(dest / 'myproject')
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
    def test_gh_missing_raises_on_list_repos(self) -> None:
        mgr = GhManager()
        with (
            patch('athome.git_managers.gh.shutil.which', return_value=None),
            pytest.raises(ToolNotFoundError),
        ):
            mgr.list_repos()

    def test_gh_error_names_tool(self) -> None:
        mgr = GhManager()
        with (
            patch('athome.git_managers.gh.shutil.which', return_value=None),
            pytest.raises(ToolNotFoundError) as exc_info,
        ):
            mgr.clone('https://github.com/org/repo')
        assert 'gh' in exc_info.value.format_message()

    def test_gh_error_includes_install_hint(self) -> None:
        mgr = GhManager()
        with (
            patch('athome.git_managers.gh.shutil.which', return_value=None),
            pytest.raises(ToolNotFoundError) as exc_info,
        ):
            mgr.create_repo('my-repo')
        assert 'cli.github.com' in exc_info.value.format_message()

    def test_git_missing_raises_on_sync_workspace(self, tmp_path: Path) -> None:
        mgr = GhManager()

        def _gh_only(tool: str) -> str | None:
            return '/usr/bin/gh' if tool == 'gh' else None

        stub = MagicMock(return_value=MagicMock(stdout='git@github.com:org/repo.git\n'))
        with (
            patch('athome.git_managers.gh.shutil.which', side_effect=_gh_only),
            patch('athome.git_managers.gh.subprocess.run', stub),
            pytest.raises(ToolNotFoundError) as exc_info,
        ):
            mgr.sync_workspace('https://github.com/org', tmp_path / 'ws')
        assert 'git' in exc_info.value.format_message()

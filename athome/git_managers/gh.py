"""GitManager implementation backed by the gh CLI."""

from __future__ import annotations

import shutil
import subprocess  # nosec
from pathlib import Path

from athome.exceptions import ToolNotFoundError
from athome.interfaces.git_manager import GitManager

_GH_HINT = 'https://cli.github.com/'
_GIT_HINT = 'https://git-scm.com/'


class GhManager(GitManager):
    """GitHub repository manager backed by the gh CLI.

    Delegates all git/API operations to the gh binary so that authentication
    is handled by `gh auth` and no tokens are stored in athome config.
    """

    def _run(self, *args: str) -> None:
        if not shutil.which('gh'):
            raise ToolNotFoundError('gh', _GH_HINT)
        subprocess.run(['gh', *args], check=True)  # noqa: S603 # nosec

    def _git(self, *args: str) -> None:
        if not shutil.which('git'):
            raise ToolNotFoundError('git', _GIT_HINT)
        subprocess.run(['git', *args], check=True)  # noqa: S603 # nosec

    def list_repos(self, owner: str | None = None) -> None:
        """List repositories, optionally filtered by *owner*."""
        args = ['repo', 'list']
        if owner:
            args.append(owner)
        self._run(*args)

    def clone(self, repo_url: str, destination: Path | None = None) -> None:
        """Clone *repo_url* into *destination*."""
        args = ['repo', 'clone', repo_url]
        if destination:
            args.append(str(destination))
        self._run(*args)

    def sync_workspace(self, owner_url: str, destination: Path) -> None:
        """Clone or pull all repos from *owner_url* into *destination*.

        For each repository returned by `gh repo list <owner>`, the directory
        is cloned on first run or updated via `git pull` on subsequent runs.
        Non-destructive: existing local modifications are never discarded.
        """
        destination.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(  # noqa: S603 # nosec
            [
                'gh',
                'repo',
                'list',
                owner_url,
                '--json',
                'sshUrl',
                '--limit',
                '1000',
                '-q',
                '.[].sshUrl',
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        repo_urls = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        for url in repo_urls:
            repo_name = url.rstrip('/').split('/')[-1].removesuffix('.git')
            repo_path = destination / repo_name
            if repo_path.exists():
                self._git('-C', str(repo_path), 'pull', '--ff-only')
            else:
                self._git('clone', url, str(repo_path))

    def create_repo(self, name: str, *, private: bool = True) -> None:
        """Create a new remote repository named *name*."""
        visibility = '--private' if private else '--public'
        self._run('repo', 'create', name, visibility)

"""Homebrew-backed developer tool manager."""

from __future__ import annotations

import subprocess  # nosec
from pathlib import Path

from athome.definitions.managers.base import BaseManager
from athome.definitions.managers.base import RequireInstalled

_INSTALL_HINT = 'https://brew.sh/'

# `brew bundle cleanup` without --force: 0 = nothing to do, 1 = listed work.
_CLEANUP_DRY_RUN_OK = (0, 1)


class BrewManager(BaseManager):
    """Developer tool manager backed by the Homebrew CLI.

    Manifest-based installs use a Brewfile; upgrades and version pinning
    delegate to the `brew` CLI directly.
    """

    REQUIRES = [RequireInstalled('brew', _INSTALL_HINT)]

    def _run(self, *args: str) -> None:
        self.fallback_require_tool()
        subprocess.run(['brew', *args], check=True)  # noqa: S603 # nosec

    def sync(self, manifest: Path) -> None:
        """Install packages declared in the Brewfile at *manifest*."""
        self._run('bundle', 'install', '--file', str(manifest))

    def upgrade(self, tool: str | None = None) -> None:
        """Upgrade *tool* (or all formulae) to their latest versions."""
        args = ('upgrade', tool) if tool else ('upgrade',)
        self._run(*args)

    def use(self, tool: str, version: str, *, global_scope: bool = False) -> None:
        """Install the versioned formula *tool*@*version*.

        Homebrew does not distinguish local vs. global scope; *global_scope* is ignored.
        """
        self._run('install', f'{tool}@{version}')

    def list_tools(self) -> None:
        """Print all installed Homebrew formulae and casks."""
        self._run('list')

    def doctor(self) -> None:
        """Run Homebrew diagnostics."""
        self._run('doctor')

    def cleanup(self, manifest: Path, *, force: bool = False) -> None:
        """Remove formulae/casks not declared in the Brewfile at *manifest*.

        Without *force*, brew's own default behavior applies: list what would
        be removed without actually removing it.

        That dry run exits 1 whenever it found something to remove — a report,
        not a failure — so it is the one brew invocation that cannot go through
        `_run`'s `check=True`. Letting it raise meant the listing succeeded only
        when it had nothing to say, and otherwise surfaced as a traceback.
        Anything other than 0 or 1 is still a real error.
        """
        args = ['bundle', 'cleanup', f'--file={manifest}']
        if force:
            args.append('--force')
            self._run(*args)
            return

        self.fallback_require_tool()
        result = subprocess.run(['brew', *args], check=False)  # noqa: S603 # nosec
        if result.returncode not in _CLEANUP_DRY_RUN_OK:
            raise subprocess.CalledProcessError(result.returncode, result.args)

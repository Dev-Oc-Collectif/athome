"""Homebrew-backed developer tool manager."""

from __future__ import annotations

import subprocess  # nosec
from pathlib import Path

from athome.definitions.managers.base import BaseManager
from athome.definitions.managers.base import RequireInstalled

_INSTALL_HINT = 'https://brew.sh/'


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
        """
        args = ['bundle', 'cleanup', f'--file={manifest}']
        if force:
            args.append('--force')
        self._run(*args)

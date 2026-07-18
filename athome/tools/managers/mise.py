"""ToolManager implementation backed by mise."""

from __future__ import annotations

import subprocess  # nosec
from pathlib import Path

from athome.definitions.managers.base import RequireInstalled
from athome.definitions.managers.tool import ToolManager

_INSTALL_HINT = 'https://mise.jdx.dev/'


class MiseToolManager(ToolManager):
    """Developer tool version manager backed by the mise CLI.

    All configuration changes go through `mise` itself so that the underlying
    mise/config.toml file is patched non-destructively — no hand-rolling TOML
    writes that could corrupt pre-existing settings.
    """

    REQUIRES = [RequireInstalled('mise', _INSTALL_HINT)]

    def _run(self, *args: str) -> None:
        subprocess.run(['mise', *args], check=True)  # noqa: S603 # nosec

    def sync(self, manifest: Path) -> None:
        """Install / sync tools declared in *manifest*."""
        self._run('install', '--config', str(manifest))

    def upgrade(self, tool: str | None = None) -> None:
        """Upgrade *tool* (or all tools) to their latest versions."""
        args = ('upgrade', '--yes', tool) if tool else ('upgrade', '--yes')
        self._run(*args)

    def use(self, tool: str, version: str, *, global_scope: bool = False) -> None:
        """Pin *tool* to *version* in the local or global mise config."""
        scope_flag = '--global' if global_scope else '--local'
        self._run('use', scope_flag, f'{tool}@{version}')

    def list_tools(self) -> None:
        """Print installed tools and their active versions."""
        self._run('list')

    def doctor(self) -> None:
        """Run mise self-diagnostics."""
        self._run('doctor')

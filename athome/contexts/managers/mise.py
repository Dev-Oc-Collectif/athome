"""EnvManager implementation backed by mise."""

from __future__ import annotations

import subprocess  # nosec

from athome.definitions.managers.base import RequireInstalled
from athome.definitions.managers.context import ContextManager

_INSTALL_HINT = 'https://mise.jdx.dev/'


class MiseEnvManager(ContextManager):
    """Shell environment manager backed by the mise CLI.

    ``load`` marks the .mise.toml in the current directory as trusted so that
    mise can activate its environment. ``activate`` prints the mise shell hook
    so the caller can eval it in their rc file.
    """

    REQUIRES = [RequireInstalled('mise', _INSTALL_HINT)]

    def _run(self, *args: str) -> None:
        subprocess.run(['mise', *args], check=True)  # noqa: S603 # nosec

    def load(self) -> None:
        """Trust the .mise.toml in the current directory."""
        self._run('trust')

    def activate(self, shell: str = 'bash') -> None:
        """Print the mise shell integration hook for *shell*."""
        self._run('activate', shell)

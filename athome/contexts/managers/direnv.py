"""EnvManager implementation backed by direnv."""

from __future__ import annotations

import subprocess  # nosec

from athome.definitions.managers.base import RequireInstalled
from athome.definitions.managers.context import ContextManager

_INSTALL_HINT = 'https://direnv.net/'


class DirenvManager(ContextManager):
    """Shell context loader backed by direnv.

    ``load`` evaluates the current .envrc and exports the resulting variables
    into the process environment. ``activate`` hooks direnv into the shell rc
    so that it activates automatically on directory change.
    """

    REQUIRES = [RequireInstalled('direnv', _INSTALL_HINT)]

    def _run(self, *args: str) -> None:
        subprocess.run(['direnv', *args], check=True)  # noqa: S603 # nosec

    def load(self) -> None:
        """Allow and evaluate the .envrc in the current directory."""
        self._run('allow')
        self._run('exec', '.', 'true')

    def activate(self, shell: str = 'bash') -> None:
        """Print the direnv hook for *shell* to stdout."""
        self._run('hook', shell)

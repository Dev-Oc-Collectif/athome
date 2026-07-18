"""Interface contract for environment variable and shell context managers."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from athome.definitions.managers.base import BaseManager


class ContextManager(BaseManager, ABC):
    """Abstract backend for exposing environment variables and shell context.

    Default implementations: mise (env vars), direnv (context loader).
    """

    DOMAIN_LABEL = "Context"
    CONFIG_ATTR = "contexts"
    NAMESPACE = "athome.context"

    @abstractmethod
    def load(self) -> None:
        """Expose Athome environment variables through the active shell."""
        ...

    @abstractmethod
    def activate(self, shell: str = 'bash') -> None:
        """Configure the shell context loader for *shell* (e.g. bash, zsh, fish)."""
        ...

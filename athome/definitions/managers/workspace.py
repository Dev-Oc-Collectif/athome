"""Interface contract for remote git repository managers."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from pathlib import Path

from athome.definitions.managers.base import BaseManager


class WorkspaceManager(BaseManager, ABC):
    """Abstract backend for managing remote git repositories.

    Default implementation: gh (GitHub CLI).

    A single manager instance may handle multiple providers (github, gitlab…).
    Owner groups and individual repository mappings are resolved from
    AthomeConfig.git before being passed to these methods.
    """

    @abstractmethod
    def list_repos(self, owner: str | None = None) -> None:
        """List repositories, optionally filtered by *owner* handle."""
        ...

    @abstractmethod
    def clone(self, repo_url: str, destination: Path | None = None) -> None:
        """Clone *repo_url* into *destination* (defaults to current directory)."""
        ...

    @abstractmethod
    def sync(self, owner_url: str, destination: Path) -> None:
        """Clone or pull all repositories belonging to *owner_url* into *destination*."""
        ...

    @abstractmethod
    def create_repo(self, name: str, *, private: bool = True) -> None:
        """Create a new remote repository named *name*."""
        ...

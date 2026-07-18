"""Interface contract for shared dotfile / configuration file managers."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

from athome.definitions.managers.base import BaseManager

if TYPE_CHECKING:
    from athome.definitions.config import ProfileConfig


class ProfileManager(BaseManager, ABC):
    """Abstract backend for managing shared files across developer machines.

    Default implementation: chezmoi.

    Each method is scoped to a *profile* so that a single machine can maintain
    several isolated sets of managed files (e.g. "work", "personal").
    The isolation is achieved via backend-specific path flags derived from
    the profile's source and destination settings.
    """

    DOMAIN_LABEL = 'Profile'
    CONFIG_ATTR = 'profles'
    NAMESPACE = 'athome.profile'

    @abstractmethod
    def init(self, profile: ProfileConfig) -> None:
        """Clone the remote dotfiles repository for *profile* without applying."""
        ...

    @abstractmethod
    def is_initialized(self, profile: ProfileConfig) -> bool:
        """Return True if the source directory for *profile* has been set up."""
        ...

    @abstractmethod
    def sync(self, profile: ProfileConfig) -> None:
        """Pull remote changes and apply them for *profile*."""
        ...

    @abstractmethod
    def apply(self, profile: ProfileConfig) -> None:
        """Apply locally staged managed files to the filesystem."""
        ...

    @abstractmethod
    def add(self, profile: ProfileConfig, path: Path) -> None:
        """Begin tracking *path* under *profile*."""
        ...

    @abstractmethod
    def diff(self, profile: ProfileConfig) -> None:
        """Print a diff of pending changes for *profile*."""
        ...

    @abstractmethod
    def status(self, profile: ProfileConfig) -> None:
        """Print the current status of managed files for *profile*."""
        ...

    @abstractmethod
    def list_pending_paths(self, profile: ProfileConfig) -> list[Path]:
        """Return target paths that will be modified or deleted by the next apply.

        Only paths that currently exist on disk are returned — callers use this
        list to decide what to back up before applying changes.
        """
        ...

    @abstractmethod
    def backup(self, profile: ProfileConfig, backup_dir: Path) -> int:
        """Snapshot files that will be touched by the next apply into *backup_dir*.

        Returns the count of files actually copied.
        """
        ...

    @abstractmethod
    def unapply(self, profile: ProfileConfig, safe_paths: frozenset[Path]) -> None:
        """Remove files introduced by *profile* that are not in *safe_paths*.

        *safe_paths* is the union of managed paths for all profiles remaining
        active after the switch — never remove those files.
        """
        ...

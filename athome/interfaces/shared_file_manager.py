"""Interface contract for shared dotfile / configuration file managers."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from athome.config import ProfileConfig


class SharedFileManager(ABC):
    """Abstract backend for managing shared files across developer machines.

    Default implementation: chezmoi.

    Each method is scoped to a *profile* so that a single machine can maintain
    several isolated sets of managed files (e.g. "work", "personal").
    The isolation is achieved via backend-specific path flags derived from
    the profile's source and destination settings.
    """

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

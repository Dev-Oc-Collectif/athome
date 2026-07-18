"""Interface contract for developer tool / runtime version managers."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from pathlib import Path

from athome.definitions.managers.base import BaseManager


class ToolManager(BaseManager, ABC):
    """Abstract backend for managing developer runtimes and CLI tools.

    Default implementation: mise.

    All mutations patch existing configuration files non-destructively.
    """

    DOMAIN_LABEL = 'Tool'
    CONFIG_ATTR = 'tools'
    NAMESPACE = 'athome.tool'

    @abstractmethod
    def sync(self, manifest: Path) -> None:
        """Install / sync tools declared in *manifest*."""
        ...

    @abstractmethod
    def upgrade(self, tool: str | None = None) -> None:
        """Upgrade *tool* (or all tools when *tool* is None) to their latest versions."""
        ...

    @abstractmethod
    def use(self, tool: str, version: str, *, global_scope: bool = False) -> None:
        """Pin *tool* to *version* locally (or globally when *global_scope* is True)."""
        ...

    @abstractmethod
    def list_tools(self) -> None:
        """Print all currently installed tools and their active versions."""
        ...

    @abstractmethod
    def doctor(self) -> None:
        """Run backend self-diagnostics and report any missing prerequisites."""
        ...

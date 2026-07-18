"""Plugin registry — discovers manager implementations via entry points."""

from __future__ import annotations

import importlib.metadata
from functools import cache

from athome.definitions.managers.base import BaseManager


@cache
def _load_managers[T: BaseManager](manager_cls: type[T]) -> dict[str, T]:
    managers = {
        ep.name: ep.load() for ep in importlib.metadata.entry_points(group=manager_cls.NAMESPACE)
    }
    return managers


class ManagersRegistry[T: BaseManager]:
    """Load and cache manager implementations registered as entry points.

    Usage::

        registry: ManagersRegistry[WorkspaceManager] = ManagersRegistry(
            'athome.workspaces.managers'
        )
        manager = registry.get('chezmoi')
    """

    def __init__(self, manager_type: type[T]) -> None:
        self.manager_type = manager_type

    @property
    def DOMAIN_LABEL(self) -> str:
        return self.manager_type.DOMAIN_LABEL

    @property
    def NAMESPACE(self) -> str:
        return self.manager_type.NAMESPACE

    @property
    def CONFIG_ATTR(self) -> str:
        return self.manager_type.CONFIG_ATTR

    def _load(self) -> dict[str, T]:
        return _load_managers(self.manager_type)

    def get(self, name: str) -> T:
        """Return the manager registered under *name*, instantiating it once."""
        managers = self._load()
        if name not in managers:
            available = ', '.join(managers) or '(none)'
            msg = (
                f"No '{name}' manager found in entry point group '{self.manager_type.NAMESPACE}'. "
                f'Available: {available}'
            )
            raise KeyError(msg)
        return managers[name]

    def all(self) -> dict[str, T]:
        """Return all registered managers, keyed by entry point name."""
        return self._load()

"""Interface contract for project scaffolding / template engines."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from pathlib import Path


class TemplateEngine(ABC):
    """Abstract backend for creating and updating projects from templates.

    Default implementation: copier.

    Templates are identified by their git repository URL. The mapping from a
    short human-readable name to a URL is resolved by the caller (typically
    from AthomeConfig.templates) before being passed here.
    """

    @abstractmethod
    def create(
        self,
        template_url: str,
        destination: Path,
        *,
        data: dict[str, str] | None = None,
        trust: bool = False,
    ) -> None:
        """Scaffold a new project from *template_url* into *destination*.

        *data* overrides template answer prompts. *trust* allows the
        template's declared tasks/hooks to run (maps to copier's
        ``unsafe``); engines without an equivalent gate accept and ignore it.
        """
        ...

    @abstractmethod
    def update(
        self,
        destination: Path,
        *,
        data: dict[str, str] | None = None,
        trust: bool = False,
    ) -> None:
        """Update an existing project in *destination* to the latest template."""
        ...

    @abstractmethod
    def is_initialized(self, destination: Path) -> bool:
        """Return True if *destination* has already been scaffolded by this engine."""
        ...

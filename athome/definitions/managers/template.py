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

    DOMAIN_LABEL = "Template"
    CONFIG_ATTR = "templates"
    NAMESPACE = "athome.template"

    @abstractmethod
    def create(self, template_url: str, destination: Path) -> None:
        """Scaffold a new project from *template_url* into *destination*."""
        ...

    @abstractmethod
    def update(self, destination: Path) -> None:
        """Update an existing project in *destination* to the latest template."""
        ...

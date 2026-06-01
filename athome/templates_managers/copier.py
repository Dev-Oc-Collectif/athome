"""TemplateEngine implementation backed by copier."""

from __future__ import annotations

from pathlib import Path

import copier

from athome.interfaces.template_engine import TemplateEngine


class CopierEngine(TemplateEngine):
    """Project scaffolding engine that delegates to the copier library."""

    def create(self, template_url: str, destination: Path) -> None:
        """Scaffold a new project from *template_url* into *destination*."""
        copier.run_copy(template_url, str(destination))

    def update(self, destination: Path) -> None:
        """Update an existing copier project in *destination*."""
        copier.run_update(str(destination))

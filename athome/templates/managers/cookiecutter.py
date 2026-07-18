"""TemplateEngine implementation backed by cruft (cookiecutter with update support)."""

from __future__ import annotations

from pathlib import Path

import cruft

from athome.definitions.managers.template import TemplateEngine


class CookieCutterEngine(TemplateEngine):
    """Project scaffolding engine that delegates to the cruft library.

    cruft wraps cookiecutter and additionally tracks the template origin so
    that ``update`` can apply upstream changes non-destructively.
    """

    def create(self, template_url: str, destination: Path) -> None:
        """Scaffold a new project from *template_url* into *destination*."""
        cruft.create(template_git_url=template_url, output_dir=destination)

    def update(self, destination: Path) -> None:
        """Update an existing cruft project in *destination* to the latest template."""
        cruft.update(project_dir=destination)

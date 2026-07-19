"""TemplateEngine implementation backed by copier."""

from __future__ import annotations

from pathlib import Path

import copier

from athome.definitions.managers.template import TemplateEngine

_ANSWERS_FILE = '.copier-answers.yml'


class CopierEngine(TemplateEngine):
    """Project scaffolding engine that delegates to the copier library."""

    def create(
        self,
        template_url: str,
        destination: Path,
        *,
        data: dict[str, str] | None = None,
        trust: bool = False,
    ) -> None:
        """Scaffold a new project from *template_url* into *destination*."""
        copier.run_copy(template_url, str(destination), data=data, unsafe=trust)

    def update(
        self,
        destination: Path,
        *,
        data: dict[str, str] | None = None,
        trust: bool = False,
    ) -> None:
        """Update an existing copier project in *destination*."""
        copier.run_update(str(destination), data=data, unsafe=trust)

    def is_initialized(self, destination: Path) -> bool:
        """Return True if *destination* has a copier answers file."""
        return (destination / _ANSWERS_FILE).exists()

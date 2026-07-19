"""TemplateEngine implementation backed by cruft (cookiecutter with update support)."""

from __future__ import annotations

from pathlib import Path

import cruft

from athome.definitions.managers.template import TemplateEngine

_CRUFT_MARKER = '.cruft.json'


class CookieCutterEngine(TemplateEngine):
    """Project scaffolding engine that delegates to the cruft library.

    cruft wraps cookiecutter and additionally tracks the template origin so
    that ``update`` can apply upstream changes non-destructively. cruft has
    no equivalent to copier's task-trust gate — cookiecutter hooks always run
    unconditionally if present — so *trust* is accepted but has no effect.
    """

    def create(
        self,
        template_url: str,
        destination: Path,
        *,
        data: dict[str, str] | None = None,
        trust: bool = False,
    ) -> None:
        """Scaffold a new project from *template_url* into *destination*."""
        del trust  # no-op: cookiecutter hooks always run, there is no gate to pass
        cruft.create(template_git_url=template_url, output_dir=destination, extra_context=data)

    def update(
        self,
        destination: Path,
        *,
        data: dict[str, str] | None = None,
        trust: bool = False,
    ) -> None:
        """Update an existing cruft project in *destination* to the latest template."""
        del trust  # no-op, see create()
        cruft.update(project_dir=destination, extra_context=data)

    def is_initialized(self, destination: Path) -> bool:
        """Return True if *destination* has a cruft tracking marker."""
        return (destination / _CRUFT_MARKER).exists()

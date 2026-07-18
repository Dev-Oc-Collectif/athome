"""Project commands — scaffold and update projects via the TemplateEngine."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from athome.definitions.config import load_config
from athome.templates.managers import CopierEngine

app = typer.Typer(help='Bootstrap and update projects from templates.')

_engine = CopierEngine()


@app.command()
def create(
    template: Annotated[
        str, typer.Argument(help='Template name (from config) or a direct git URL')
    ],
    destination: Annotated[Path, typer.Argument(help='Destination directory')],
) -> None:
    """Scaffold a new project from a named template or a direct git URL."""
    cfg = load_config()
    tmpl = cfg.templates.get(template)
    url = tmpl.source if tmpl is not None else template
    typer.echo(f'Creating project from {url} → {destination}')
    _engine.create(url, destination)


@app.command()
def update(
    destination: Annotated[Path, typer.Argument(help='Existing project directory')] = Path('.'),
) -> None:
    """Update an existing copier project to the latest template version."""
    typer.echo(f'Updating project in {destination}')
    _engine.update(destination)

"""Project commands — scaffold and update projects via the TemplateEngine."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from athome.definitions.config import load_config
from athome.templates.managers.cookiecutter import CookieCutterEngine
from athome.templates.managers.copier import CopierEngine

app = typer.Typer(help='Bootstrap and update projects from templates (copier or cruft).')

_ENGINES = {'copier': CopierEngine(), 'cruft': CookieCutterEngine()}


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
    manager = tmpl.manager if tmpl is not None else 'copier'
    engine = _ENGINES.get(manager)
    if engine is None:
        typer.echo(f'Unknown template engine "{manager}". Supported: {", ".join(_ENGINES)}')
        raise typer.Exit(1)
    typer.echo(f'Creating project from {url} → {destination} (via {manager})')
    engine.create(url, destination)


@app.command()
def update(
    destination: Annotated[Path, typer.Argument(help='Existing project directory')] = Path('.'),
    manager: Annotated[
        str, typer.Option('--manager', '-m', help='Template engine that created this project.')
    ] = 'copier',
) -> None:
    """Update an existing project to the latest template version."""
    engine = _ENGINES.get(manager)
    if engine is None:
        typer.echo(f'Unknown template engine "{manager}". Supported: {", ".join(_ENGINES)}')
        raise typer.Exit(1)
    typer.echo(f'Updating project in {destination} (via {manager})')
    engine.update(destination)

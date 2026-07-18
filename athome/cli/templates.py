"""Template commands — inspect and register available project templates."""

from __future__ import annotations

from typing import Annotated

import typer

from athome.definitions import config_writer
from athome.definitions.config import CONFIG_PATH
from athome.definitions.config import load_config

app = typer.Typer(help='Inspect and register available project templates.')

_KNOWN_MANAGERS = frozenset({'copier', 'cruft'})


@app.command('list')
def list_templates() -> None:
    """List all templates defined in config.toml."""
    cfg = load_config()
    if not cfg.templates:
        typer.echo(
            'No templates configured. Add entries to the [templates] section of config.toml.'
        )
        return
    for name, tmpl in cfg.templates.items():
        typer.echo(f'  {name:<24} [{tmpl.manager}]  {tmpl.source}')


@app.command()
def add(
    name: Annotated[str, typer.Argument(help='New template name to add to config.toml')],
    source: Annotated[str, typer.Argument(help='Git repository URL for the template')],
    manager: Annotated[
        str, typer.Option('--manager', '-m', help='Template engine: copier or cruft.')
    ] = 'copier',
) -> None:
    """Register a new template in config.toml."""
    if manager not in _KNOWN_MANAGERS:
        typer.echo(
            f'Unknown manager "{manager}". Supported: {", ".join(sorted(_KNOWN_MANAGERS))}',
            err=True,
        )
        raise typer.Exit(1)
    config_writer.add_template(name, source, manager=manager, path=CONFIG_PATH)
    typer.echo(f"Added template '{name}' to {CONFIG_PATH}.")

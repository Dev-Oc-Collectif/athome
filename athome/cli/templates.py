"""Template commands — inspect available project templates from config."""

from __future__ import annotations

import typer

from athome.definitions.config import load_config

app = typer.Typer(help='Inspect available project templates.')


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

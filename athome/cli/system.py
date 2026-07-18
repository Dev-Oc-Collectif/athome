"""System commands — health checks for athome's required backends."""

from __future__ import annotations

import shutil

import typer

app = typer.Typer(help='System health checks.')

_REQUIRED_TOOLS = ('chezmoi', 'gh', 'brew', 'mise')


@app.command()
def doctor() -> None:
    """Check that all required athome tools are present on PATH."""
    all_ok = True
    for tool in _REQUIRED_TOOLS:
        if shutil.which(tool):
            typer.echo(f'  ✓  {tool}')
        else:
            typer.echo(f'  ✗  {tool}  (missing)')
            all_ok = False

    if not all_ok:
        raise typer.Exit(1)

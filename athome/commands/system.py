"""System commands — health checks and tool upgrades via the EnvManager."""

from __future__ import annotations

import shutil

import typer

from athome.env_managers import MiseManager

app = typer.Typer(help='System health checks and tool management (default backend: mise).')

_mise = MiseManager()

_REQUIRED_TOOLS = ('uv', 'just', 'mise', 'chezmoi', 'gh', 'direnv')


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


@app.command()
def upgrade() -> None:
    """Upgrade all managed runtimes and tools via mise."""
    if not shutil.which('mise'):
        typer.echo('mise is not installed — cannot upgrade tools.', err=True)
        raise typer.Exit(1)
    typer.echo('Upgrading tools via mise...')
    _mise.upgrade()

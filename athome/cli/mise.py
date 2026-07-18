"""Mise commands — keep mise configuration aligned across chezmoi profiles."""

from __future__ import annotations

import typer

from athome.definitions.config import load_config
from athome.tools.mise_align import find_drift

app = typer.Typer(help='Keep mise configuration aligned across profiles.')


@app.command()
def check() -> None:
    """Report tools pinned to different versions across configured profiles."""
    cfg = load_config()
    if not cfg.profiles:
        typer.echo('No profiles configured. Add entries to the [profiles] section of config.toml.')
        return

    drifts = find_drift(cfg.profiles)
    if not drifts:
        typer.echo('mise configuration is aligned across all profiles.')
        return

    typer.echo('Version drift detected:')
    for drift in drifts:
        typer.echo(f'  {drift.tool}:')
        for profile_name, version in sorted(drift.versions.items()):
            typer.echo(f'    {profile_name:<20} {version}')
    raise typer.Exit(1)

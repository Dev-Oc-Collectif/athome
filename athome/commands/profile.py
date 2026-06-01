"""Profile commands — manage dotfile profiles via the SharedFileManager."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from athome.config import ProfileConfig
from athome.config import load_config
from athome.files_managers import ChezmoidManager

app = typer.Typer(help='Manage dotfile profiles (default backend: chezmoi).')

_manager = ChezmoidManager()


def _resolve_profile(name: str) -> ProfileConfig:
    """Return the ProfileConfig for *name*, aborting with a message when absent."""
    cfg = load_config()
    if name not in cfg.profiles:
        defined = ', '.join(cfg.profiles) or '(none)'
        typer.echo(f"Profile '{name}' not found. Defined profiles: {defined}", err=True)
        raise typer.Exit(1)
    return cfg.profiles[name]


@app.command()
def sync(
    name: Annotated[str, typer.Argument(help='Profile name as defined in config.toml')],
) -> None:
    """Pull remote changes and apply managed files for a profile."""
    profile = _resolve_profile(name)
    typer.echo(f'Syncing profile: {name}')
    _manager.sync(profile)


@app.command()
def apply(
    name: Annotated[str, typer.Argument(help='Profile name as defined in config.toml')],
) -> None:
    """Apply locally staged managed files to the filesystem."""
    profile = _resolve_profile(name)
    typer.echo(f'Applying profile: {name}')
    _manager.apply(profile)


@app.command()
def add(
    name: Annotated[str, typer.Argument(help='Profile name as defined in config.toml')],
    path: Annotated[Path, typer.Argument(help='File or directory to track')],
) -> None:
    """Start tracking a file under a profile."""
    profile = _resolve_profile(name)
    _manager.add(profile, path)


@app.command()
def diff(
    name: Annotated[str, typer.Argument(help='Profile name as defined in config.toml')],
) -> None:
    """Show pending changes for a profile."""
    profile = _resolve_profile(name)
    _manager.diff(profile)


@app.command()
def status(
    name: Annotated[str, typer.Argument(help='Profile name as defined in config.toml')],
) -> None:
    """Show managed files status for a profile."""
    profile = _resolve_profile(name)
    _manager.status(profile)


@app.command('list')
def list_profiles() -> None:
    """List all profiles defined in config.toml."""
    cfg = load_config()
    if not cfg.profiles:
        typer.echo('No profiles defined. Add entries to the [profiles] section of config.toml.')
        return
    for profile in cfg.profiles.values():
        dest = f' (dest: {profile.destination})' if profile.destination else ''
        typer.echo(f'  {profile.name}  →  {profile.source}{dest}')

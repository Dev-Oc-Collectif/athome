"""Profile commands — manage dotfile profiles via the SharedFileManager."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from athome.definitions import config_writer
from athome.definitions.config import CONFIG_PATH
from athome.definitions.config import ProfileConfig
from athome.definitions.config import load_config
from athome.profiles.managers.chezmoi import ChezmoiManager

app = typer.Typer(help='Manage dotfile profiles (backend: chezmoi).')

_manager = ChezmoiManager()


def _resolve_profile(name: str) -> ProfileConfig:
    """Return the ProfileConfig for *name*, aborting with a message when absent."""
    cfg = load_config()
    if name not in cfg.profiles:
        defined = ', '.join(cfg.profiles) or '(none)'
        typer.echo(f"Profile '{name}' not found. Defined profiles: {defined}", err=True)
        raise typer.Exit(1)
    return cfg.profiles[name]


def _assert_initialized(profile: ProfileConfig, manager: ChezmoiManager) -> None:
    """Abort with a helpful message when a profile's source directory has not been set up."""
    if not manager.is_initialized(profile):
        typer.echo(
            f"Profile '{profile.name}' is not initialized. Run: athome profile init {profile.name}",
            err=True,
        )
        raise typer.Exit(1)


@app.command()
def add(
    name: Annotated[str, typer.Argument(help='New profile name to add to config.toml')],
    source: Annotated[str, typer.Argument(help='Git repository URL for the profile')],
    destination: Annotated[
        Path | None,
        typer.Option(
            '--destination', help='Custom source checkout path (overrides the XDG default).'
        ),
    ] = None,
    loads: Annotated[
        str | None,
        typer.Option('--loads', help='Comma-separated profile names this profile depends on.'),
    ] = None,
) -> None:
    """Register a new profile in config.toml (does not init or apply it)."""
    loads_list = [item.strip() for item in loads.split(',') if item.strip()] if loads else []
    config_writer.add_profile(
        name,
        source,
        destination=str(destination) if destination else None,
        loads=loads_list,
        path=CONFIG_PATH,
    )
    typer.echo(f"Added profile '{name}' to {CONFIG_PATH}. Run 'athome profile init {name}' next.")


@app.command()
def init(
    name: Annotated[str, typer.Argument(help='Profile name as defined in config.toml')],
) -> None:
    """Clone the remote dotfiles repository for a profile (required before apply/sync)."""
    profile = _resolve_profile(name)
    manager = _manager
    if manager.is_initialized(profile):
        typer.echo(f"Profile '{name}' is already initialized.")
        return
    typer.echo(f'Initializing profile: {name}')
    manager.init(profile)
    typer.echo(f"Done. Run 'athome profile apply {name}' to apply managed files.")


@app.command()
def sync(
    name: Annotated[str, typer.Argument(help='Profile name as defined in config.toml')],
) -> None:
    """Pull remote changes and apply managed files for a profile."""
    profile = _resolve_profile(name)
    manager = _manager
    _assert_initialized(profile, manager)
    typer.echo(f'Syncing profile: {name}')
    manager.sync(profile)


@app.command()
def apply(
    name: Annotated[str, typer.Argument(help='Profile name as defined in config.toml')],
) -> None:
    """Apply locally staged managed files to the filesystem."""
    profile = _resolve_profile(name)
    manager = _manager
    _assert_initialized(profile, manager)
    typer.echo(f'Applying profile: {name}')
    manager.apply(profile)


@app.command('apply-all')
def apply_all() -> None:
    """Initialize (if needed) and apply every configured profile, in config.toml order.

    Unconditional — no diffing against a previous stack, no backup, no unapply.
    Safe only for additive chezmoi setups.
    """
    cfg = load_config()
    if not cfg.profiles:
        typer.echo('No profiles defined. Add one with `athome profile add`.')
        return
    manager = _manager
    for profile in cfg.profiles.values():
        if not manager.is_initialized(profile):
            typer.echo(f'Initializing: {profile.name}')
            manager.init(profile)
        typer.echo(f'Applying: {profile.name}')
        manager.apply(profile)
    typer.echo(f'Applied {len(cfg.profiles)} profile(s): {", ".join(cfg.profiles)}')


@app.command()
def track(
    name: Annotated[str, typer.Argument(help='Profile name as defined in config.toml')],
    path: Annotated[Path, typer.Argument(help='File or directory to track')],
) -> None:
    """Start tracking a file under a profile (chezmoi add)."""
    profile = _resolve_profile(name)
    manager = _manager
    _assert_initialized(profile, manager)
    manager.add(profile, path)


@app.command()
def diff(
    name: Annotated[str, typer.Argument(help='Profile name as defined in config.toml')],
) -> None:
    """Show pending changes for a profile."""
    profile = _resolve_profile(name)
    manager = _manager
    _assert_initialized(profile, manager)
    manager.diff(profile)


@app.command()
def status(
    name: Annotated[str, typer.Argument(help='Profile name as defined in config.toml')],
) -> None:
    """Show managed files status for a profile."""
    profile = _resolve_profile(name)
    manager = _manager
    _assert_initialized(profile, manager)
    manager.status(profile)


@app.command('list')
def list_profiles() -> None:
    """List all profiles defined in config.toml."""
    cfg = load_config()
    if not cfg.profiles:
        typer.echo(
            'No profiles defined. Add entries to the [profiles] section of config.toml '
            '(or run `athome profile add`).'
        )
        return
    for profile in cfg.profiles.values():
        dest = f' (dest: {profile.destination})' if profile.destination else ''
        loads = f' [loads: {", ".join(profile.loads)}]' if profile.loads else ''
        typer.echo(f'  {profile.name}  →  {profile.source}{dest}{loads}')

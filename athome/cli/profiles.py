"""Profile commands — manage dotfile profiles via the SharedFileManager."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from athome.definitions.config import PROFILES_SOURCE_BASE
from athome.definitions.config import ProfileConfig
from athome.definitions.config import load_config
from athome.definitions.managers.profile import ProfileManager
from athome.definitions.registry import ManagersRegistry
from athome.profiles.orchestrator import AthomeState
from athome.profiles.orchestrator import compute_switch
from athome.profiles.orchestrator import load_state
from athome.profiles.orchestrator import resolve_stack
from athome.profiles.orchestrator import save_state

app = typer.Typer(help='Manage dotfile profiles (default backend: chezmoi).')

_registry = ManagersRegistry(ProfileManager)


def _resolve_profile(name: str) -> ProfileConfig:
    """Return the ProfileConfig for *name*, aborting with a message when absent."""
    cfg = load_config()
    if name not in cfg.profiles:
        defined = ', '.join(cfg.profiles) or '(none)'
        typer.echo(f"Profile '{name}' not found. Defined profiles: {defined}", err=True)
        raise typer.Exit(1)
    return cfg.profiles[name]


def _get_manager(profile: ProfileConfig) -> ProfileManager:
    """Resolve the SharedFileManager for *profile* via the registry."""
    try:
        return _registry.get(profile.manager)
    except KeyError as err:
        typer.echo(
            f"No manager '{profile.manager}' available for profile '{profile.name}'. "
            f'Install the required package or check your config.',
            err=True,
        )
        raise typer.Exit(1) from err


def _assert_initialized(profile: ProfileConfig, manager: ProfileManager) -> None:
    """Abort with a helpful message when a profile's source directory has not been set up."""
    if not manager.is_initialized(profile):
        typer.echo(
            f"Profile '{profile.name}' is not initialized. Run: athome profile init {profile.name}",
            err=True,
        )
        raise typer.Exit(1)


def _run_backup(profile: ProfileConfig, manager: ProfileManager, backup_name: str) -> None:
    """Snapshot files that will change; logs results to stdout."""
    backup_dir = PROFILES_SOURCE_BASE / backup_name
    count = manager.backup(profile, backup_dir)
    typer.echo(f'Backed up {count} file(s) to {backup_dir}')


@app.command()
def init(
    name: Annotated[str, typer.Argument(help='Profile name as defined in config.toml')],
) -> None:
    """Clone the remote dotfiles repository for a profile (required before apply/sync)."""
    profile = _resolve_profile(name)
    manager = _get_manager(profile)
    if manager.is_initialized(profile):
        typer.echo(f"Profile '{name}' is already initialized.")
        return
    typer.echo(f'Initializing profile: {name}')
    manager.init(profile)
    typer.echo(f"Done. Run 'athome profile apply {name}' to apply managed files.")


@app.command()
def sync(
    name: Annotated[str, typer.Argument(help='Profile name as defined in config.toml')],
    backup: Annotated[
        bool,
        typer.Option(
            '--backup/--no-backup',
            help='Snapshot files that will change before syncing.',
        ),
    ] = False,
    backup_name: Annotated[
        str | None,
        typer.Option(
            '--backup-name',
            metavar='NAME',
            help='Custom backup folder name (implies --backup).',
        ),
    ] = None,
) -> None:
    """Pull remote changes and apply managed files for a profile."""
    profile = _resolve_profile(name)
    manager = _get_manager(profile)
    _assert_initialized(profile, manager)
    if backup or backup_name is not None:
        folder = backup_name or f'backup-before-sync-{name}'
        _run_backup(profile, manager, folder)
    typer.echo(f'Syncing profile: {name}')
    manager.sync(profile)


@app.command()
def apply(
    name: Annotated[str, typer.Argument(help='Profile name as defined in config.toml')],
    backup: Annotated[
        bool,
        typer.Option(
            '--backup/--no-backup',
            help='Snapshot files that will change before applying.',
        ),
    ] = False,
    backup_name: Annotated[
        str | None,
        typer.Option(
            '--backup-name',
            metavar='NAME',
            help='Custom backup folder name (implies --backup).',
        ),
    ] = None,
) -> None:
    """Apply locally staged managed files to the filesystem."""
    profile = _resolve_profile(name)
    manager = _get_manager(profile)
    _assert_initialized(profile, manager)
    if backup or backup_name is not None:
        folder = backup_name or f'backup-before-apply-{name}'
        _run_backup(profile, manager, folder)
    typer.echo(f'Applying profile: {name}')
    manager.apply(profile)


@app.command()
def add(
    name: Annotated[str, typer.Argument(help='Profile name as defined in config.toml')],
    path: Annotated[Path, typer.Argument(help='File or directory to track')],
) -> None:
    """Start tracking a file under a profile."""
    profile = _resolve_profile(name)
    manager = _get_manager(profile)
    _assert_initialized(profile, manager)
    manager.add(profile, path)


@app.command()
def diff(
    name: Annotated[str, typer.Argument(help='Profile name as defined in config.toml')],
) -> None:
    """Show pending changes for a profile."""
    profile = _resolve_profile(name)
    manager = _get_manager(profile)
    _assert_initialized(profile, manager)
    manager.diff(profile)


@app.command()
def status(
    name: Annotated[str, typer.Argument(help='Profile name as defined in config.toml')],
) -> None:
    """Show managed files status for a profile."""
    profile = _resolve_profile(name)
    manager = _get_manager(profile)
    _assert_initialized(profile, manager)
    manager.status(profile)


@app.command()
def unapply(
    name: Annotated[str, typer.Argument(help='Profile name to unapply')],
) -> None:
    """Remove files introduced by a profile, preserving files from other active profiles."""
    cfg = load_config()
    profile = _resolve_profile(name)
    manager = _get_manager(profile)

    state = load_state()
    remaining = {p for p in state.active_profiles if p != name}
    safe_paths: frozenset[Path] = frozenset(
        path
        for pname in remaining
        if pname in cfg.profiles
        for path in _get_manager(cfg.profiles[pname]).list_pending_paths(cfg.profiles[pname])
    )

    typer.echo(f'Unapplying profile: {name}')
    manager.unapply(profile, safe_paths)

    new_active = [p for p in state.active_profiles if p != name]
    save_state(AthomeState(active_profiles=new_active))
    typer.echo(f"Profile '{name}' unapplied.")


@app.command()
def switch(
    name: Annotated[str, typer.Argument(help='Profile name to switch to')],
    backup: Annotated[
        bool,
        typer.Option(
            '--backup/--no-backup',
            help='Snapshot files before applying the new profile.',
        ),
    ] = True,
) -> None:
    """Switch to a profile, unapplying removed profiles and applying new ones.

    Computes the full dependency stack for the target profile (via its ``loads``
    list), diffs against the currently active stack, unapplies profiles that are
    leaving the stack (in reverse order), and applies those being added.
    """
    cfg = load_config()
    if name not in cfg.profiles:
        defined = ', '.join(cfg.profiles) or '(none)'
        typer.echo(f"Profile '{name}' not found. Defined profiles: {defined}", err=True)
        raise typer.Exit(1)

    state = load_state()
    new_stack = resolve_stack(name, cfg.profiles)
    to_unapply, to_apply, remaining = compute_switch(state.active_profiles, new_stack)

    safe_paths: frozenset[Path] = frozenset(
        path
        for pname in remaining | set(to_apply)
        if pname in cfg.profiles
        for path in _get_manager(cfg.profiles[pname]).list_pending_paths(cfg.profiles[pname])
    )

    for pname in to_unapply:
        if pname not in cfg.profiles:
            typer.echo(f"Warning: profile '{pname}' not in config, skipping unapply.", err=True)
            continue
        p = cfg.profiles[pname]
        typer.echo(f'Unapplying: {pname}')
        _get_manager(p).unapply(p, safe_paths)

    for pname in to_apply:
        if pname not in cfg.profiles:
            typer.echo(f"Warning: profile '{pname}' not in config, skipping apply.", err=True)
            continue
        p = cfg.profiles[pname]
        manager = _get_manager(p)
        if not manager.is_initialized(p):
            typer.echo(f'Initializing: {pname}')
            manager.init(p)
        if backup:
            folder = f'backup-before-switch-{pname}'
            _run_backup(p, manager, folder)
        typer.echo(f'Applying: {pname}')
        manager.apply(p)

    save_state(AthomeState(active_profiles=new_stack))
    typer.echo(f'Switched to profile stack: {" → ".join(new_stack)}')


@app.command('list')
def list_profiles() -> None:
    """List all profiles defined in config.toml."""
    cfg = load_config()
    state = load_state()
    active = set(state.active_profiles)
    if not cfg.profiles:
        typer.echo('No profiles defined. Add entries to the [profiles] section of config.toml.')
        return
    for profile in cfg.profiles.values():
        marker = ' *' if profile.name in active else ''
        dest = f' (dest: {profile.destination})' if profile.destination else ''
        loads = f' [loads: {", ".join(profile.loads)}]' if profile.loads else ''
        typer.echo(f'  {profile.name}  →  {profile.source}{dest}{loads}{marker}')

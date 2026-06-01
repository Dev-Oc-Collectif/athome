"""Workspace commands — mass clone/pull git organisations."""

from __future__ import annotations

from importlib import import_module
from importlib.metadata import entry_points
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Annotated
from typing import Any

import typer

from athome.config import load_config

if TYPE_CHECKING:
    from athome.interfaces.git_manager import GitManager

app = typer.Typer(help='Manage workspace repositories.')


def _discover_managers() -> dict[str, GitManager]:
    """Load GitManager implementations registered via the athome.git_managers entry point."""
    return {ep.name: ep.load()() for ep in entry_points(group='athome.git_managers')}


def _load_managers_from_config(overrides: dict[str, str]) -> dict[str, Any]:
    """Instantiate managers specified as importable class paths in [managers] config."""
    result: dict[str, Any] = {}
    for name, class_path in overrides.items():
        module_path, _, class_name = class_path.rpartition(':')
        if not module_path or not class_name:
            typer.echo(f'Warning: invalid manager path "{class_path}" for "{name}"', err=True)
            continue
        try:
            mod = import_module(module_path)
        except ImportError:
            typer.echo(f'Warning: cannot import "{module_path}" for manager "{name}"', err=True)
            continue
        cls = getattr(mod, class_name, None)
        if cls is None:
            typer.echo(f'Warning: "{class_name}" not found in "{module_path}"', err=True)
            continue
        result[name] = cls()
    return result


_MANAGERS: dict[str, Any] = _discover_managers()


@app.command()
def sync(
    destination: Annotated[
        Path | None,
        typer.Option('--dest', '-d', help='Root directory that receives cloned repos.'),
    ] = None,
) -> None:
    """Clone or pull all repositories from every configured git owner.

    The provider key in [git.owners.<provider>] selects which manager to use.
    Defaults to git.workspace from config when --dest is not given.
    Unknown providers are skipped with a warning.
    """
    cfg = load_config()
    dest = destination or cfg.git.workspace
    managers = {**_MANAGERS, **_load_managers_from_config(cfg.managers)}

    if not cfg.git.owners:
        typer.echo(
            'No git owners configured. Add entries to a [git.owners.*] section of config.toml.',
            err=True,
        )
        raise typer.Exit(1)

    for provider, owners in cfg.git.owners.items():
        manager = managers.get(provider)
        if manager is None:
            typer.echo(
                f'Unknown provider "{provider}". Supported: {", ".join(managers)}',
                err=True,
            )
            continue
        for handle, url in owners.items():
            target = dest / provider / handle
            typer.echo(f'Syncing {provider}/{handle} → {target}')
            manager.sync_workspace(url, target)

    for provider, repos in cfg.git.repositories.items():
        manager = managers.get(provider)
        if manager is None:
            typer.echo(
                f'Unknown provider "{provider}". Supported: {", ".join(managers)}',
                err=True,
            )
            continue
        for name, url in repos.items():
            typer.echo(f'Cloning individual repo {provider}/{name}')
            manager.clone(url, dest / provider / name)


@app.command('list')
def list_repos(
    provider: Annotated[
        str | None,
        typer.Argument(help='Provider key (e.g. gh). Omit to list all configured providers.'),
    ] = None,
    owner: Annotated[
        str | None,
        typer.Option('--owner', help='Filter repositories by owner handle.'),
    ] = None,
) -> None:
    """List remote repositories.

    Without a provider argument, prints every provider key found in config.toml.
    With a provider, delegates to that manager's list command.
    """
    if provider is None:
        cfg = load_config()
        all_providers = sorted(set(cfg.git.owners) | set(cfg.git.repositories))
        if not all_providers:
            typer.echo('No git providers configured in config.toml.', err=True)
            raise typer.Exit(1)
        for p in all_providers:
            typer.echo(p)
        return

    cfg = load_config()
    managers = {**_MANAGERS, **_load_managers_from_config(cfg.managers)}
    manager = managers.get(provider)
    if manager is None:
        typer.echo(
            f'Unknown provider "{provider}". Supported: {", ".join(managers)}',
            err=True,
        )
        raise typer.Exit(1)
    manager.list_repos(owner)

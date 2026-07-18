"""Workspace commands — mass clone/pull git organisations."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Annotated
from typing import Any

import typer

from athome.definitions.config import load_config
from athome.definitions.registry import ManagersRegistry

if TYPE_CHECKING:
    from athome.definitions.managers.workspace import WorkspaceManager

app = typer.Typer(help='Manage workspace repositories.')

_registry: ManagersRegistry[WorkspaceManager] = ManagersRegistry('athome.git_managers')


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


@app.command()
def sync(
    destination: Annotated[
        Path | None,
        typer.Option('--dest', '-d', help='Root directory that receives cloned repos.'),
    ] = None,
) -> None:
    """Clone or pull all repositories from every configured owner.

    Each entry in [workspace.owners] names an owner (org/user) with a source URL
    and the manager backend to use. Repos are cloned under dest/<owner-name>/.
    """
    cfg = load_config()
    dest = destination or cfg.workspace.destination.target
    managers: dict[str, Any] = {**_registry.all(), **_load_managers_from_config(cfg.managers)}

    if not cfg.workspace.owners:
        typer.echo(
            'No workspace owners configured. '
            'Add entries to the [workspace.owners] section of config.toml.',
            err=True,
        )
        raise typer.Exit(1)

    for owner_name, owner_cfg in cfg.workspace.owners.items():
        manager = managers.get(owner_cfg.manager)
        if manager is None:
            typer.echo(
                f'Unknown manager "{owner_cfg.manager}" for owner "{owner_name}". '
                f'Supported: {", ".join(managers)}',
                err=True,
            )
            continue
        target = dest / owner_name
        typer.echo(f'Syncing {owner_name} → {target}')
        manager.sync(owner_cfg.source, target)

    for repo_name, repo_cfg in cfg.workspace.repos.items():
        manager = managers.get(repo_cfg.manager)
        if manager is None:
            typer.echo(
                f'Unknown manager "{repo_cfg.manager}" for repo "{repo_name}". '
                f'Supported: {", ".join(managers)}',
                err=True,
            )
            continue
        typer.echo(f'Cloning repo {repo_name}')
        manager.clone(repo_cfg.source, dest / repo_name)


@app.command('list')
def list_repos(
    owner: Annotated[
        str | None,
        typer.Argument(help='Owner name from config. Omit to list all configured owners.'),
    ] = None,
) -> None:
    """List configured workspace owners, or repos for a specific owner.

    Without an argument, prints every owner entry from config.toml.
    With an owner name, delegates to that owner's manager to list its repositories.
    """
    cfg = load_config()
    if owner is None:
        all_owners = sorted(cfg.workspace.owners)
        if not all_owners and not cfg.workspace.repos:
            typer.echo('No git owners configured in config.toml.', err=True)
            raise typer.Exit(1)
        for name in all_owners:
            owner_cfg = cfg.workspace.owners[name]
            typer.echo(f'  {name}  [{owner_cfg.manager}]  →  {owner_cfg.source}')
        return

    if owner not in cfg.workspace.owners:
        typer.echo(
            f'Owner "{owner}" not found. Configured: {", ".join(cfg.workspace.owners) or "(none)"}',
            err=True,
        )
        raise typer.Exit(1)

    owner_cfg = cfg.workspace.owners[owner]
    managers: dict[str, Any] = {**_registry.all(), **_load_managers_from_config(cfg.managers)}
    manager = managers.get(owner_cfg.manager)
    if manager is None:
        typer.echo(
            f'Unknown manager "{owner_cfg.manager}". Supported: {", ".join(managers)}',
            err=True,
        )
        raise typer.Exit(1)
    manager.list_repos(None)

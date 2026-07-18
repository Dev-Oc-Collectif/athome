"""Repo commands — manage and mass-sync remote git repositories (backend: gh)."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from athome.definitions import config_writer
from athome.definitions.config import CONFIG_PATH
from athome.definitions.config import load_config
from athome.workspaces.managers import GhManager

app = typer.Typer(help='Manage remote repositories (backend: gh).')

_manager = GhManager()


@app.command('add-owner')
def add_owner(
    name: Annotated[str, typer.Argument(help='Owner key name in config.toml')],
    source: Annotated[str, typer.Argument(help='Owner handle or URL (e.g. an org/user name)')],
) -> None:
    """Register a new workspace owner in config.toml."""
    config_writer.add_owner(name, source, path=CONFIG_PATH)
    typer.echo(f"Added owner '{name}' to {CONFIG_PATH}.")


@app.command('add-repo')
def add_repo(
    name: Annotated[str, typer.Argument(help='Repo key name in config.toml')],
    source: Annotated[str, typer.Argument(help='Repository URL or OWNER/NAME')],
) -> None:
    """Register a new individually-tracked repository in config.toml."""
    config_writer.add_repo(name, source, path=CONFIG_PATH)
    typer.echo(f"Added repo '{name}' to {CONFIG_PATH}.")


@app.command()
def create(
    name: Annotated[str, typer.Argument(help='Repository name')],
    public: Annotated[bool, typer.Option('--public', help='Create as a public repository')] = False,
) -> None:
    """Create a new remote repository."""
    typer.echo(f'Creating {"public" if public else "private"} repo: {name}')
    _manager.create_repo(name, private=not public)


@app.command()
def clone(
    url: Annotated[str, typer.Argument(help='Repository URL or OWNER/NAME to clone')],
    destination: Annotated[
        Path | None, typer.Argument(help='Destination directory (defaults to CWD)')
    ] = None,
) -> None:
    """Clone a single repository."""
    typer.echo(f'Cloning {url}' + (f' → {destination}' if destination else ''))
    _manager.clone(url, destination)


@app.command('list')
def list_repos(
    owner: Annotated[str | None, typer.Argument(help='Filter by owner handle')] = None,
) -> None:
    """List remote repositories, optionally filtered by owner."""
    _manager.list_repos(owner)


@app.command()
def sync(
    destination: Annotated[
        Path | None,
        typer.Option('--dest', '-d', help='Root directory that receives cloned repos.'),
    ] = None,
) -> None:
    """Clone or pull every repository declared under workspace.owners / workspace.repos.

    Repos belonging to a configured owner are cloned under dest/<owner-name>/;
    individually configured repos are cloned under dest/<repo-name>.
    """
    cfg = load_config()
    dest = destination or cfg.workspace.destination.target

    if not cfg.workspace.owners and not cfg.workspace.repos:
        typer.echo(
            'Nothing configured to sync. Add entries to [workspace.owners] or '
            '[workspace.repos] in config.toml.',
            err=True,
        )
        raise typer.Exit(1)

    for owner_name, owner_cfg in cfg.workspace.owners.items():
        target = dest / owner_name
        typer.echo(f'Syncing {owner_name} → {target}')
        _manager.sync(owner_cfg.source, target)

    for repo_name, repo_cfg in cfg.workspace.repos.items():
        typer.echo(f'Cloning repo {repo_name}')
        _manager.clone(repo_cfg.source, dest / repo_name)

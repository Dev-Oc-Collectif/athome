"""Repo commands — manage remote git repositories via the GitManager."""

from __future__ import annotations

from typing import Annotated

import typer

from athome.git_managers import GhManager

app = typer.Typer(help='Manage remote repositories (default backend: gh).')

_manager = GhManager()


@app.command()
def create(
    name: Annotated[str, typer.Argument(help='Repository name')],
    public: Annotated[bool, typer.Option('--public', help='Create as a public repository')] = False,
) -> None:
    """Create a new remote repository."""
    typer.echo(f'Creating {"public" if public else "private"} repo: {name}')
    _manager.create_repo(name, private=not public)


@app.command('list')
def list_repos(
    owner: Annotated[str | None, typer.Argument(help='Filter by owner handle')] = None,
) -> None:
    """List remote repositories."""
    _manager.list_repos(owner)

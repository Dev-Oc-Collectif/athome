"""Config commands — manage the athome configuration file."""

from __future__ import annotations

import os
import subprocess  # nosec
from typing import Annotated

import typer

from athome.config import CONFIG_PATH

app = typer.Typer(help='Manage athome configuration.')

_TEMPLATE = """\
# athome configuration — place at ~/.config/athome/config.toml

[profiles]
# Simple form: just a source URL.
# work = "https://github.com/your-org/dotfiles-work"
# Rich form: source + optional local destination for chezmoi source files.
# personal = {source = "https://github.com/your-user/dotfiles-personal", destination = "~/.dots"}

[templates]
# python = "https://github.com/Dev-Oc-Collectif/python-template"
# zola   = "https://github.com/Dev-Oc-Collectif/zola-template"

[git]
# workspace = "~/workspace"   # default clone destination for all providers

[git.owners.gh]
# my-org = "https://github.com/my-org"

[git.repositories.gh]
# dotfiles = "https://github.com/your-user/dotfiles"

# [managers]
# Override or extend auto-discovered git managers.
# gitlab = "athome_gitlab:GitLabManager"
"""


@app.command()
def init(
    force: Annotated[bool, typer.Option('--force', help='Overwrite existing config.')] = False,
) -> None:
    """Create a starter config.toml at the default config path."""
    if CONFIG_PATH.exists() and not force:
        typer.echo(
            f'Config already exists at {CONFIG_PATH}. Use --force to overwrite.',
            err=True,
        )
        raise typer.Exit(1)
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(_TEMPLATE)
    typer.echo(f'Config created at {CONFIG_PATH}')


@app.command()
def show() -> None:
    """Print the current configuration file."""
    if not CONFIG_PATH.exists():
        typer.echo(
            f'No config file at {CONFIG_PATH}. Run `athome setup` to create one.',
            err=True,
        )
        raise typer.Exit(1)
    typer.echo(CONFIG_PATH.read_text())


@app.command()
def edit() -> None:
    """Open the config file in $VISUAL / $EDITOR (falls back to vi)."""
    if not CONFIG_PATH.exists():
        typer.echo(
            f'No config file at {CONFIG_PATH}. Run `athome setup` to create one first.',
            err=True,
        )
        raise typer.Exit(1)
    editor = os.environ.get('VISUAL') or os.environ.get('EDITOR') or 'vi'
    subprocess.run([editor, str(CONFIG_PATH)], check=False)  # noqa: S603 # nosec

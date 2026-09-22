"""Devbox commands — provision the dev userspace an immutable host cannot provide."""

from __future__ import annotations

from typing import Annotated

import typer

from athome.definitions.config import load_config
from athome.profiles.managers.chezmoi import ChezmoiManager
from athome.tools.cleanup import collect_devbox_packages
from athome.tools.managers.dnf import DnfManager

app = typer.Typer(help='Provision the development container (backend: dnf in distrobox).')

DEFAULT_BOX = 'dev'

_manager = DnfManager()


def _declared() -> set[str]:
    cfg = load_config()
    if not cfg.profiles:
        typer.echo('No profiles configured. Add entries to the profiles section of config.toml.')
        raise typer.Exit(1)
    return collect_devbox_packages(ChezmoiManager(), cfg.profiles)


@app.command()
def sync(
    box: Annotated[str, typer.Option('--box', help='Dev box name.')] = DEFAULT_BOX,
) -> None:
    """Install every package declared across profiles into the dev box."""
    packages = _declared()
    if not packages:
        typer.echo('No .dnf fragments found across configured profiles.')
        return
    typer.echo(f'Installing {len(packages)} declared package(s) into {box}...')
    _manager.sync(box, sorted(packages))


@app.command()
def cleanup(
    box: Annotated[str, typer.Option('--box', help='Dev box name.')] = DEFAULT_BOX,
    force: Annotated[
        bool, typer.Option('--force', help='Actually remove (default: dry-run/list only).')
    ] = False,
) -> None:
    """Remove packages from the dev box that no profile declares any more."""
    extra = _manager.cleanup(box, _declared(), force=force)
    if not extra:
        typer.echo(f'{box}: nothing installed that no profile declares.')
        return
    verb = 'Removed' if force else 'Would remove'
    typer.echo(f'{verb} from {box}:')
    for name in extra:
        typer.echo(f'  {name}')

"""Cleanup command — reconcile installed state against every configured profile.

Three domains, each owned by the manager that can both install and remove in
it: brew on the host, mise for runtimes, and dnf inside the dev box. A domain
that only ever installs accumulates packages nobody can account for later.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Annotated

import typer

from athome.definitions.config import ProfileConfig
from athome.definitions.config import load_config
from athome.profiles.managers.chezmoi import ChezmoiManager
from athome.tools.cleanup import build_combined_brewfile
from athome.tools.cleanup import collect_brew_fragments
from athome.tools.cleanup import collect_devbox_packages
from athome.tools.cleanup import run_mise_prune
from athome.tools.managers.brew import BrewManager
from athome.tools.managers.dnf import DnfManager


def _cleanup_brew(
    chezmoi: ChezmoiManager, profiles: dict[str, ProfileConfig], *, force: bool
) -> None:
    fragments = collect_brew_fragments(chezmoi, profiles)
    if not fragments:
        typer.echo('No Brewfile fragments found across configured profiles.')
        return
    if not shutil.which('brew'):
        typer.echo('brew is not installed — skipping brew cleanup.', err=True)
        return
    tmp = Path(tempfile.mkstemp(suffix='.Brewfile')[1])
    tmp.write_text(build_combined_brewfile(fragments))
    try:
        typer.echo(f'Running brew bundle cleanup ({len(fragments)} fragment(s))...')
        BrewManager().cleanup(tmp, force=force)
    finally:
        tmp.unlink(missing_ok=True)


def _cleanup_mise(*, force: bool) -> None:
    if not shutil.which('mise'):
        typer.echo('mise is not installed — skipping mise prune.', err=True)
        return
    typer.echo('Running mise prune...')
    run_mise_prune(force=force)


def _cleanup_devbox(
    chezmoi: ChezmoiManager, profiles: dict[str, ProfileConfig], box: str, *, force: bool
) -> None:
    if not shutil.which('distrobox'):
        typer.echo('distrobox is not installed — skipping dev box cleanup.', err=True)
        return
    declared = collect_devbox_packages(chezmoi, profiles)
    if not declared:
        typer.echo('No .dnf fragments found across configured profiles.')
        return
    extra = DnfManager().cleanup(box, declared, force=force)
    if not extra:
        typer.echo(f'Dev box {box}: nothing installed that no profile declares.')
        return
    verb = 'Removed' if force else 'Would remove'
    typer.echo(f'{verb} from dev box {box}: {", ".join(extra)}')


def cleanup(
    force: Annotated[
        bool,
        typer.Option('--force', help='Actually remove things (default: dry-run/list only).'),
    ] = False,
    skip_brew: Annotated[bool, typer.Option('--skip-brew', help='Skip the brew side.')] = False,
    skip_mise: Annotated[bool, typer.Option('--skip-mise', help='Skip the mise side.')] = False,
    skip_devbox: Annotated[
        bool, typer.Option('--skip-devbox', help='Skip the dev box side.')
    ] = False,
    box: Annotated[str, typer.Option('--box', help='Dev box name.')] = 'dev',
) -> None:
    """Reconcile installed brew/mise state against every configured profile.

    Brew: aggregates every profile's brew file.d Brewfile fragments (whether or
    not that profile is currently applied) into one combined manifest and runs
    `brew bundle cleanup` against it once.

    Mise: runs `mise prune` directly — mise already resolves every currently
    applied profile's conf.d fragment from ~/.config/mise/conf.d/ on its own,
    so no aggregation is needed (or reliably possible) on athome's side.

    Non-destructive by default — pass --force to actually remove things.
    """
    cfg = load_config()
    if not cfg.profiles:
        typer.echo('No profiles configured. Add entries to the profiles section of config.toml.')
        raise typer.Exit(1)

    chezmoi = ChezmoiManager()

    if not skip_brew:
        _cleanup_brew(chezmoi, cfg.profiles, force=force)
    if not skip_mise:
        _cleanup_mise(force=force)
    if not skip_devbox:
        _cleanup_devbox(chezmoi, cfg.profiles, box, force=force)

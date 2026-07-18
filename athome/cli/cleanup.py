"""Cleanup command — reconcile installed brew/mise state against every profile."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Annotated

import typer

from athome.definitions.config import load_config
from athome.profiles.managers.chezmoi import ChezmoiManager
from athome.tools.cleanup import build_combined_brewfile
from athome.tools.cleanup import collect_brew_fragments
from athome.tools.cleanup import run_mise_prune
from athome.tools.managers.brew import BrewManager


def cleanup(
    force: Annotated[
        bool,
        typer.Option('--force', help='Actually remove things (default: dry-run/list only).'),
    ] = False,
    skip_brew: Annotated[bool, typer.Option('--skip-brew', help='Skip the brew side.')] = False,
    skip_mise: Annotated[bool, typer.Option('--skip-mise', help='Skip the mise side.')] = False,
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

    if not skip_brew:
        chezmoi = ChezmoiManager()
        fragments = collect_brew_fragments(chezmoi, cfg.profiles)
        if not fragments:
            typer.echo('No Brewfile fragments found across configured profiles.')
        elif not shutil.which('brew'):
            typer.echo('brew is not installed — skipping brew cleanup.', err=True)
        else:
            combined = build_combined_brewfile(fragments)
            tmp = Path(tempfile.mkstemp(suffix='.Brewfile')[1])
            tmp.write_text(combined)
            try:
                typer.echo(f'Running brew bundle cleanup ({len(fragments)} fragment(s))...')
                BrewManager().cleanup(tmp, force=force)
            finally:
                tmp.unlink(missing_ok=True)

    if not skip_mise:
        if not shutil.which('mise'):
            typer.echo('mise is not installed — skipping mise prune.', err=True)
        else:
            typer.echo('Running mise prune...')
            run_mise_prune(force=force)

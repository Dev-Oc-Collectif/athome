"""Bootstrap command — the one entry point that breaks the config circularity.

~/.config/athome/config.toml cannot itself declare where to find the profile
repos it's meant to describe: on a brand new machine there's no config file
yet, so athome has no way to know where to clone anything from. The only way
out is a single external input (the personal profile's URL, given by hand or
piped from a bootstrap.sh), from which everything else is discovered:

  1. Register + clone the personal profile from that one URL.
  2. Read <personal source>/athome.toml — a repo-root file, git-tracked, but
     living *outside* .chezmoiroot so chezmoi structurally cannot see or
     deploy it. It declares the profiles/templates/workspace entries this
     machine should also know about (e.g. the devoc and secondbrain
     profiles), without personal itself owning ~/.config/athome/config.toml.
  3. Merge those entries into the local config, once. Local entries always
     win on a name conflict — a machine can override or omit anything the
     personal repo suggests.

Applying anything is a deliberately separate step (`athome profile
apply-all`) — bootstrap only gets every profile registered and personal
cloned.
"""

from __future__ import annotations

import tomllib
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import Annotated
from typing import Any

import typer

from athome.definitions import config_writer
from athome.definitions.config import CONFIG_PATH
from athome.definitions.config import AthomeConfig
from athome.definitions.config import load_config
from athome.definitions.config import profile_source_path
from athome.exceptions import ConfigEntryExistsError
from athome.profiles.managers.chezmoi import ChezmoiManager

_manager = ChezmoiManager()

_ATHOME_TOML = 'athome.toml'


def _contributed_destination(athome_toml: Path) -> str | None:
    """Read a bare [workspace] destination straight out of the raw TOML.

    AthomeConfig.workspace.destination always has a value (it defaults to
    ~/workspace when unset), so going through the typed config can't tell
    "not declared" from "declared as the default" — the raw dict can.
    """
    raw: dict[str, Any] = tomllib.loads(athome_toml.read_text())
    destination_raw: Any = raw.get('workspace', {}).get('destination')
    if destination_raw is None:
        return None
    if isinstance(destination_raw, str):
        return destination_raw
    return str(destination_raw['target'])


def _merge_entry(add: Callable[[], None], echo_message: str) -> None:
    """Run *add*, echoing *echo_message* unless the entry already exists locally.

    Local entries always win on conflict — that's what the swallowed
    ConfigEntryExistsError means here.
    """
    try:
        add()
    except ConfigEntryExistsError:
        return
    typer.echo(echo_message)


def _merge_contributed(contributed: AthomeConfig, athome_toml: Path) -> None:
    """Write every entry from *contributed* into the local config."""
    destination = _contributed_destination(athome_toml)
    if destination is not None:
        _merge_entry(
            partial(config_writer.add_destination, destination, path=CONFIG_PATH),
            f'  + workspace destination -> {destination}',
        )

    for name, profile in contributed.profiles.items():
        _merge_entry(
            partial(
                config_writer.add_profile,
                name,
                profile.source,
                destination=str(profile.destination) if profile.destination else None,
                path=CONFIG_PATH,
            ),
            f"  + profile '{name}' -> {profile.source}",
        )

    for name, template in contributed.templates.items():
        _merge_entry(
            partial(
                config_writer.add_template,
                name,
                template.source,
                manager=template.manager,
                path=CONFIG_PATH,
            ),
            f"  + template '{name}' -> {template.source}",
        )

    for name, owner in contributed.workspace.owners.items():
        _merge_entry(
            partial(config_writer.add_owner, name, owner.source, path=CONFIG_PATH),
            f"  + workspace owner '{name}' -> {owner.source}",
        )

    for name, repo in contributed.workspace.repos.items():
        _merge_entry(
            partial(config_writer.add_repo, name, repo.source, path=CONFIG_PATH),
            f"  + workspace repo '{name}' -> {repo.source}",
        )

    for name, brew_entry in contributed.brew.items():
        _merge_entry(
            partial(config_writer.add_brew_entry, name, str(brew_entry.manifest), path=CONFIG_PATH),
            f"  + brew '{name}' -> {brew_entry.manifest}",
        )


def bootstrap(
    source: Annotated[str, typer.Argument(help='Git URL for your personal profile')],
) -> None:
    """One-time setup for a brand new machine.

    Registers and clones the *personal* profile from SOURCE, then merges in
    whatever additional profiles/templates/workspace entries its repo-root
    athome.toml declares. Does not apply anything — run `athome profile
    apply-all` afterwards.
    """
    try:
        config_writer.add_profile('personal', source, path=CONFIG_PATH)
        typer.echo(f"Registered profile 'personal' -> {source}")
    except ConfigEntryExistsError:
        typer.echo("Profile 'personal' is already registered, leaving it as-is.")

    cfg = load_config(CONFIG_PATH)
    personal = cfg.profiles.get('personal')
    if personal is None:
        typer.echo(
            "Profile 'personal' is registered under a different source than expected — "
            'check config.toml.',
            err=True,
        )
        raise typer.Exit(1)

    if _manager.is_initialized(personal):
        typer.echo("Profile 'personal' is already initialized.")
    else:
        typer.echo("Cloning profile 'personal'...")
        _manager.init(personal)

    athome_toml = profile_source_path(personal) / _ATHOME_TOML
    if not athome_toml.exists():
        typer.echo(f'No {athome_toml} found — nothing else to register.')
        return

    typer.echo(f'Merging {athome_toml}...')
    contributed = load_config(athome_toml)
    _merge_contributed(contributed, athome_toml)
    typer.echo("Bootstrap complete. Run 'athome profile apply-all' next.")

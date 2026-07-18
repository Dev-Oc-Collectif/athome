"""Brew commands — manage Homebrew packages via configured [brew] entries."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from athome.definitions import config_writer
from athome.definitions.config import CONFIG_PATH
from athome.definitions.config import BrewEntryConfig
from athome.definitions.config import load_config
from athome.tools.managers.brew import BrewManager

app = typer.Typer(help='Manage Homebrew packages from the brew config section (backend: brew).')

_manager = BrewManager()


def _resolve_entry(name: str) -> BrewEntryConfig:
    cfg = load_config()
    if name not in cfg.brew:
        defined = ', '.join(cfg.brew) or '(none)'
        typer.echo(f'Brew entry "{name}" not found. Defined: {defined}', err=True)
        raise typer.Exit(1)
    return cfg.brew[name]


@app.command()
def add(
    name: Annotated[str, typer.Argument(help='New brew entry name to add to config.toml')],
    manifest: Annotated[Path, typer.Argument(help='Path to the Brewfile manifest')],
) -> None:
    """Register a new Brewfile entry in config.toml."""
    config_writer.add_brew_entry(name, str(manifest), path=CONFIG_PATH)
    typer.echo(f"Added brew entry '{name}' to {CONFIG_PATH}.")


@app.command()
def sync(
    name: Annotated[
        str | None,
        typer.Argument(help='Brew entry name from config. Omit to sync all entries.'),
    ] = None,
) -> None:
    """Install tools from a named manifest entry (or all configured entries)."""
    cfg = load_config()
    if not cfg.brew:
        typer.echo(
            'No brew entries configured. Add entries to the [brew] section of config.toml.',
            err=True,
        )
        raise typer.Exit(1)
    if name is not None and name not in cfg.brew:
        defined = ', '.join(cfg.brew) or '(none)'
        typer.echo(f'Brew entry "{name}" not found. Defined: {defined}', err=True)
        raise typer.Exit(1)
    entries = {name: cfg.brew[name]} if name is not None else cfg.brew
    for entry_name, entry_cfg in entries.items():
        typer.echo(f'Syncing {entry_name} from {entry_cfg.manifest}')
        _manager.sync(entry_cfg.manifest)


@app.command()
def upgrade(
    name: Annotated[
        str | None,
        typer.Argument(help='Brew entry name from config. Omit to upgrade all entries.'),
    ] = None,
    tool: Annotated[
        str | None,
        typer.Option('--tool', '-t', help='Specific tool name within the entry to upgrade.'),
    ] = None,
) -> None:
    """Upgrade tools in a named entry (or all configured entries)."""
    cfg = load_config()
    if not cfg.brew:
        typer.echo('No brew entries configured.', err=True)
        raise typer.Exit(1)
    if name is not None and name not in cfg.brew:
        typer.echo(f'Brew entry "{name}" not found.', err=True)
        raise typer.Exit(1)
    entries = {name: cfg.brew[name]} if name is not None else cfg.brew
    for entry_name in entries:
        typer.echo(f'Upgrading {entry_name}')
        _manager.upgrade(tool)


@app.command('list')
def list_tools(
    name: Annotated[
        str | None,
        typer.Argument(help='Brew entry name. Omit to list all configured entries.'),
    ] = None,
) -> None:
    """List configured brew entries, or the installed tools within a specific entry."""
    cfg = load_config()
    if not cfg.brew:
        typer.echo('No brew entries configured. Add entries to the [brew] section of config.toml.')
        return
    if name is None:
        for entry_name, entry_cfg in cfg.brew.items():
            typer.echo(f'  {entry_name:<24} {entry_cfg.manifest}')
        return
    _resolve_entry(name)
    typer.echo(f'Tools in {name}:')
    _manager.list_tools()

"""Tools commands — manage developer tools via configured [tools] entries."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Annotated

import typer

from athome.definitions.config import ToolEntryConfig
from athome.definitions.config import load_config
from athome.definitions.registry import ManagersRegistry
from athome.exceptions import ToolNotFoundError

if TYPE_CHECKING:
    from athome.definitions.managers.tool import ToolManager

app = typer.Typer(help='Manage developer tools from [tools] config.')

_registry: ManagersRegistry[ToolManager] = ManagersRegistry('athome.tool_managers')


def _resolve_entry(name: str) -> ToolEntryConfig:
    cfg = load_config()
    if name not in cfg.tools:
        defined = ', '.join(cfg.tools) or '(none)'
        typer.echo(f'Tool entry "{name}" not found. Defined: {defined}', err=True)
        raise typer.Exit(1)
    return cfg.tools[name]


def _get_manager(entry: ToolEntryConfig) -> ToolManager:
    try:
        return _registry.get(entry.manager)
    except KeyError as err:
        typer.echo(
            f'No tool manager "{entry.manager}" available. '
            f'Install the required package or check your config.',
            err=True,
        )
        raise typer.Exit(1) from err
    except ToolNotFoundError as err:
        typer.echo(err.format_message(), err=True)
        raise typer.Exit(1) from err


@app.command()
def sync(
    name: Annotated[
        str | None,
        typer.Argument(help='Tool entry name from config. Omit to sync all entries.'),
    ] = None,
) -> None:
    """Install tools from a named manifest entry (or all configured entries)."""
    cfg = load_config()
    if not cfg.tools:
        typer.echo(
            'No tools configured. Add entries to the [tools] section of config.toml.',
            err=True,
        )
        raise typer.Exit(1)
    if name is not None and name not in cfg.tools:
        defined = ', '.join(cfg.tools) or '(none)'
        typer.echo(f'Tool entry "{name}" not found. Defined: {defined}', err=True)
        raise typer.Exit(1)
    entries = {name: cfg.tools[name]} if name is not None else cfg.tools
    for entry_name, entry_cfg in entries.items():
        manager = _get_manager(entry_cfg)
        typer.echo(f'Syncing {entry_name} ({entry_cfg.manager}) from {entry_cfg.manifest}')
        manager.sync(entry_cfg.manifest)


@app.command()
def upgrade(
    name: Annotated[
        str | None,
        typer.Argument(help='Tool entry name from config. Omit to upgrade all entries.'),
    ] = None,
    tool: Annotated[
        str | None,
        typer.Option('--tool', '-t', help='Specific tool name within the entry to upgrade.'),
    ] = None,
) -> None:
    """Upgrade tools in a named entry (or all configured entries)."""
    cfg = load_config()
    if not cfg.tools:
        typer.echo('No tools configured.', err=True)
        raise typer.Exit(1)
    if name is not None and name not in cfg.tools:
        typer.echo(f'Tool entry "{name}" not found.', err=True)
        raise typer.Exit(1)
    entries = {name: cfg.tools[name]} if name is not None else cfg.tools
    for entry_name, entry_cfg in entries.items():
        manager = _get_manager(entry_cfg)
        typer.echo(f'Upgrading {entry_name} ({entry_cfg.manager})')
        manager.upgrade(tool)


@app.command('list')
def list_tools(
    name: Annotated[
        str | None,
        typer.Argument(help='Tool entry name. Omit to list all configured entries.'),
    ] = None,
) -> None:
    """List configured tool entries, or the installed tools within a specific entry."""
    cfg = load_config()
    if not cfg.tools:
        typer.echo('No tools configured. Add entries to the [tools] section of config.toml.')
        return
    if name is None:
        for entry_name, entry_cfg in cfg.tools.items():
            typer.echo(f'  {entry_name:<24} [{entry_cfg.manager}]  {entry_cfg.manifest}')
        return
    entry_cfg = _resolve_entry(name)
    manager = _get_manager(entry_cfg)
    typer.echo(f'Tools in {name} ({entry_cfg.manager}):')
    manager.list_tools()

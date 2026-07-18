"""Env commands — manage shell environment contexts via configured [env] entries."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Annotated

import typer

from athome.definitions.config import EnvEntryConfig
from athome.definitions.config import load_config
from athome.definitions.registry import ManagersRegistry
from athome.exceptions import ToolNotFoundError

if TYPE_CHECKING:
    from athome.definitions.managers.context import ContextManager

app = typer.Typer(help='Manage shell environment contexts from [env] config.')

_registry: ManagersRegistry[ContextManager] = ManagersRegistry('athome.env_managers')


def _resolve_entry(name: str) -> EnvEntryConfig:
    cfg = load_config()
    if name not in cfg.env.entries:
        defined = ', '.join(cfg.env.entries) or '(none)'
        typer.echo(f'Env context "{name}" not found. Defined: {defined}', err=True)
        raise typer.Exit(1)
    return cfg.env.entries[name]


def _get_manager(entry: EnvEntryConfig) -> ContextManager:
    try:
        return _registry.get(entry.engine)
    except KeyError as err:
        typer.echo(
            f'No env manager "{entry.engine}" available. '
            f'Install the required package or check your config.',
            err=True,
        )
        raise typer.Exit(1) from err
    except ToolNotFoundError as err:
        typer.echo(err.format_message(), err=True)
        raise typer.Exit(1) from err


@app.command()
def load(
    name: Annotated[str, typer.Argument(help='Env context name from config.')],
) -> None:
    """Expose environment variables for a named context through the active shell."""
    entry = _resolve_entry(name)
    manager = _get_manager(entry)
    typer.echo(f'Loading env context: {name} ({entry.engine})')
    manager.load()


@app.command()
def activate(
    name: Annotated[str | None, typer.Argument(help='Env context name from config.')] = None,
    shell: Annotated[
        str | None,
        typer.Option('--shell', '-s', help='Shell to configure (overrides the entry default).'),
    ] = None,
) -> None:
    """Configure the shell hook for a named env context.

    Prints the hook snippet to stdout so it can be eval'd in your shell rc file.
    """
    if not name:
        for envmanager in _registry.all().values():
            envmanager.activate()
        return
    entry = _resolve_entry(name)
    manager = _get_manager(entry)
    active_shell = shell or entry.shell
    typer.echo(f'Activating env context: {name} ({entry.engine}) for {active_shell}')
    manager.activate(active_shell)


@app.command('list')
def list_envs() -> None:
    """List all env contexts defined in config.toml."""
    cfg = load_config()
    if not cfg.env.entries and not cfg.env.variables:
        typer.echo('No env contexts configured. Add entries to the [env] section of config.toml.')
        return
    if cfg.env.entries:
        for name, entry in cfg.env.entries.items():
            typer.echo(f'  {name:<24} [{entry.engine}]  shell={entry.shell}')
    if cfg.env.variables:
        typer.echo('')
        typer.echo('  Variables:')
        for var, value in cfg.env.variables.items():
            typer.echo(f'    {var}={value}')

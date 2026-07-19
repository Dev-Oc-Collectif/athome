"""Template commands — inspect, register, and use project templates."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Annotated

import typer

from athome.definitions import config_writer
from athome.definitions.config import CONFIG_PATH
from athome.definitions.config import load_config
from athome.templates.managers.cookiecutter import CookieCutterEngine
from athome.templates.managers.copier import CopierEngine

if TYPE_CHECKING:
    from athome.definitions.managers.template import TemplateEngine

app = typer.Typer(help='Inspect, register, and use project templates (copier or cruft).')

_KNOWN_MANAGERS = frozenset({'copier', 'cruft'})
_ENGINES: dict[str, TemplateEngine] = {'copier': CopierEngine(), 'cruft': CookieCutterEngine()}
_ACTIONS = frozenset({'create', 'sync', 'update'})

_DATA_OPTION = typer.Option('--data', help='Template answer override as key=value. Repeatable.')
_TRUST_OPTION = typer.Option(
    '--trust',
    help="Allow the template's declared tasks to run (copier: unsafe=True; ignored by cruft).",
)


@app.command('list')
def list_templates() -> None:
    """List all templates defined in config.toml."""
    cfg = load_config()
    if not cfg.templates:
        typer.echo(
            'No templates configured. Add entries to the [templates] section of config.toml.'
        )
        return
    for name, tmpl in cfg.templates.items():
        typer.echo(f'  {name:<24} [{tmpl.manager}]  {tmpl.source}')


@app.command()
def add(
    name: Annotated[str, typer.Argument(help='New template name to add to config.toml')],
    source: Annotated[str, typer.Argument(help='Git repository URL for the template')],
    manager: Annotated[
        str, typer.Option('--manager', '-m', help='Template engine: copier or cruft.')
    ] = 'copier',
) -> None:
    """Register a new template in config.toml."""
    if manager not in _KNOWN_MANAGERS:
        typer.echo(
            f'Unknown manager "{manager}". Supported: {", ".join(sorted(_KNOWN_MANAGERS))}',
            err=True,
        )
        raise typer.Exit(1)
    config_writer.add_template(name, source, manager=manager, path=CONFIG_PATH)
    typer.echo(f"Added template '{name}' to {CONFIG_PATH}.")


def _resolve_engine(target: str) -> tuple[str, str, TemplateEngine]:
    """Resolve *target* to (template_url, manager_name, engine).

    *target* is looked up by name in config.toml first; if not found there,
    it is treated as a direct git URL with the default 'copier' manager.
    """
    cfg = load_config()
    tmpl = cfg.templates.get(target)
    url = tmpl.source if tmpl is not None else target
    manager = tmpl.manager if tmpl is not None else 'copier'
    engine = _ENGINES.get(manager)
    if engine is None:
        typer.echo(f'Unknown template engine "{manager}". Supported: {", ".join(_ENGINES)}')
        raise typer.Exit(1)
    return url, manager, engine


def _parse_data(pairs: list[str]) -> dict[str, str]:
    """Parse repeatable ``key=value`` --data entries into a dict."""
    result: dict[str, str] = {}
    for pair in pairs:
        if '=' not in pair:
            typer.echo(f'Invalid --data entry "{pair}": expected key=value.', err=True)
            raise typer.Exit(1)
        key, value = pair.split('=', 1)
        result[key] = value
    return result


def _run_action(
    action: str,
    target: str,
    destination: Path,
    *,
    data: dict[str, str],
    trust: bool,
) -> None:
    """Resolve *target*'s engine and dispatch to create/update (sync picks one)."""
    url, manager, engine = _resolve_engine(target)
    resolved_action = action
    if action == 'sync':
        resolved_action = 'update' if engine.is_initialized(destination) else 'create'
    if resolved_action == 'create':
        typer.echo(f'Creating project from {url} → {destination} (via {manager})')
        engine.create(url, destination, data=data or None, trust=trust)
    else:
        typer.echo(f'Updating project in {destination} (via {manager})')
        engine.update(destination, data=data or None, trust=trust)


@app.command()
def use(
    target: Annotated[str, typer.Argument(help='Template name (from config) or a direct git URL')],
    action: Annotated[str, typer.Argument(help='Action to perform: create, sync, or update.')],
    destination: Annotated[Path, typer.Argument(help='Project directory')] = Path('.'),
    data: Annotated[list[str] | None, _DATA_OPTION] = None,
    trust: Annotated[bool, _TRUST_OPTION] = False,
) -> None:
    r"""Create, sync, or update a project from a named template or a direct git URL.

    The engine (copier or cruft) is always resolved from the named template's
    config.toml entry — for all three actions, not just create.

    \b
    Actions:
      create — scaffold a new project.
      update — update an existing project to the latest template.
      sync   — create if *destination* isn't yet initialized for this engine,
               otherwise update it.
    """
    if action not in _ACTIONS:
        typer.echo(f'Unknown action "{action}". Supported: {", ".join(sorted(_ACTIONS))}', err=True)
        raise typer.Exit(1)
    _run_action(action, target, destination, data=_parse_data(data or []), trust=trust)


def create(
    target: Annotated[str, typer.Argument(help='Template name (from config) or a direct git URL')],
    destination: Annotated[Path, typer.Argument(help='Destination directory')] = Path('.'),
    data: Annotated[list[str] | None, _DATA_OPTION] = None,
    trust: Annotated[bool, _TRUST_OPTION] = False,
) -> None:
    """Scaffold a new project from a named template or a direct git URL.

    Top-level shortcut for `athome template use <target> create [destination]`.
    """
    _run_action('create', target, destination, data=_parse_data(data or []), trust=trust)

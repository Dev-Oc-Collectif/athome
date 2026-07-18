"""Config commands — manage the athome configuration file."""

from __future__ import annotations

import os
import subprocess  # nosec
from typing import Annotated

import typer

from athome.definitions.config import CONFIG_PATH

app = typer.Typer(help='Manage athome configuration.')


def _prompt_entries(
    section: str,
    fields: list[tuple[str, str]],
) -> list[dict[str, str]]:
    """Prompt for repeated key-value entries until the user enters an empty name."""
    entries: list[dict[str, str]] = []
    while True:
        name = typer.prompt(f'  {section} name (empty to stop)', default='').strip()
        if not name:
            break
        entry: dict[str, str] = {'name': name}
        for field_name, field_default in fields:
            value = typer.prompt(f'    {field_name}', default=field_default).strip()
            entry[field_name] = value or field_default
        entries.append(entry)
    return entries


def _build_toml(**sections: list[dict[str, str]]) -> str:
    """Render a config.toml string from the collected interactive data."""
    lines: list[str] = ['# athome configuration — ~/.config/athome/config.toml', '']

    for key, section in sections.items():
        lines.append(f'[{key}]')
        lines.extend(
            f'{element["name"]} = {{{
                ", ".join(
                    f'{innerkey} = "{element[innerkey]}"'
                    for innerkey in element
                    if innerkey != "name"
                )
            }}}'
            for element in section
        )
        lines.append('')

    return '\n'.join(lines)


@app.command()
def init(
    force: Annotated[bool, typer.Option('--force', help='Overwrite existing config.')] = False,
) -> None:
    """Interactively create a config.toml at the default config path.

    Prompts for each section (profiles, templates, workspace, tools, env).
    Press Enter with an empty name to finish any section and move on.
    """
    if CONFIG_PATH.exists() and not force:
        typer.echo(
            f'Config already exists at {CONFIG_PATH}. Use --force to overwrite.',
            err=True,
        )
        raise typer.Exit(1)

    typer.echo(f'Creating config at {CONFIG_PATH}')
    typer.echo('Press Enter to accept defaults. Leave name empty to skip a section.')
    typer.echo('')

    configuration_data: dict[str, list[dict[str, str]]] = {}

    if typer.confirm('Configure profiles?', default=False):
        configuration_data['profiles'] = _prompt_entries(
            'Profile', [('source', ''), ('manager', 'chezmoi')]
        )

    if typer.confirm('Configure templates?', default=False):
        configuration_data['templates'] = _prompt_entries(
            'Template', [('source', ''), ('manager', 'copier')]
        )

    if typer.confirm('Configure workspace?', default=False):
        configuration_data['workspace'] = [
            {
                'name': 'destination',
                'value': typer.prompt('  Destination', default='~/workspace').strip(),
            }
        ]
        if typer.confirm('  Add workspace owners?', default=False):
            configuration_data['workspace.owners'] = _prompt_entries(
                '  Owner', [('source', ''), ('manager', 'gh')]
            )
        if typer.confirm('  Add individual repos?', default=False):
            configuration_data['workspace.repos'] = _prompt_entries(
                '  Repo', [('source', ''), ('manager', 'gh')]
            )

    if typer.confirm('Configure tools?', default=False):
        configuration_data['tools'] = _prompt_entries(
            'Tool entry', [('manager', 'mise'), ('manifest', '~/.config/athome/mise.toml')]
        )

    if typer.confirm('Configure env contexts?', default=False):
        configuration_data['env'] = _prompt_entries(
            'Env context', [('engine', 'mise'), ('shell', 'zsh')]
        )
        if typer.confirm('  Add env variables?', default=False):
            configuration_data['env.variables'] = _prompt_entries('  Variable', [('value', '')])

    content = _build_toml(**configuration_data)
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(content)
    typer.echo(f'\nConfig written to {CONFIG_PATH}')
    typer.echo("Run 'athome config show' to review it, or 'athome config edit' to tweak it.")


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

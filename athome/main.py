"""athome — developer environment orchestrator CLI entry point."""

from __future__ import annotations

import typer

from athome.commands import config as config_cmd
from athome.commands import profile
from athome.commands import project
from athome.commands import repo
from athome.commands import system
from athome.commands import template
from athome.commands import workspace

app = typer.Typer(
    name='athome',
    help="Agnostic developer environment orchestrator by Dev'Oc Collectif.",
    no_args_is_help=True,
)

app.add_typer(profile.app, name='profile', help='Manage dotfile profiles (chezmoi).')
app.add_typer(workspace.app, name='workspace', help='Mass-sync git organisations.')
app.add_typer(project.app, name='project', help='Scaffold and update projects (copier).')
app.add_typer(repo.app, name='repo', help='Manage remote git repositories (gh).')
app.add_typer(template.app, name='template', help='Inspect available project templates.')
app.add_typer(system.app, name='system', help='Health checks and tool upgrades (mise).')
app.add_typer(config_cmd.app, name='config', help='Manage athome configuration.')

# Top-level shortcut aliases
app.command(name='create', help='Scaffold a project (alias: project create).')(project.create)
app.command(name='templates', help='List templates (alias: template list).')(
    template.list_templates
)
app.command(name='setup', help='Create a starter config.toml (alias: config init).')(
    config_cmd.init
)

if __name__ == '__main__':  # pragma: no cover
    app()

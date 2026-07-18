"""athome — developer environment orchestrator CLI entry point."""

from __future__ import annotations

import typer

from athome.cli import config
from athome.cli import contexts
from athome.cli import profiles
from athome.cli import project
from athome.cli import repo
from athome.cli import system
from athome.cli import templates
from athome.cli import tools
from athome.cli import workspaces

app = typer.Typer(
    name='athome',
    help="Agnostic developer environment orchestrator by Dev'Oc Collectif.",
    no_args_is_help=True,
)

app.add_typer(profiles.app, name='profile', help='Manage dotfile profiles (chezmoi).')
app.add_typer(workspaces.app, name='workspace', help='Mass-sync git organisations.')
app.add_typer(project.app, name='project', help='Scaffold and update projects (copier).')
app.add_typer(repo.app, name='repo', help='Manage remote git repositories (gh).')
app.add_typer(templates.app, name='template', help='Inspect available project templates.')
app.add_typer(tools.app, name='tools', help='Manage developer tools (mise, brew).')
app.add_typer(contexts.app, name='env', help='Manage shell environment contexts (mise, direnv).')
app.add_typer(system.app, name='system', help='System health checks.')
app.add_typer(config.app, name='config', help='Manage athome configuration.')

# Top-level shortcut aliases
app.command(name='create', help='Scaffold a project (alias: project create).')(project.create)
app.command(name='templates', help='List templates (alias: template list).')(
    templates.list_templates
)
app.command(name='setup', help='Create a starter config.toml (alias: config init).')(config.init)

if __name__ == '__main__':  # pragma: no cover
    app()

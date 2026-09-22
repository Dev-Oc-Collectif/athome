"""athome — developer environment orchestrator CLI entry point."""

from __future__ import annotations

import typer

from athome.cli import bootstrap
from athome.cli import brew
from athome.cli import cleanup
from athome.cli import config
from athome.cli import devbox
from athome.cli import mise
from athome.cli import profiles
from athome.cli import repo
from athome.cli import system
from athome.cli import templates

app = typer.Typer(
    name='athome',
    help="Agnostic developer environment orchestrator by Dev'Oc Collectif.",
    no_args_is_help=True,
)

app.add_typer(profiles.app, name='profile', help='Manage dotfile profiles (chezmoi).')
app.add_typer(repo.app, name='repo', help='Manage and mass-sync git repositories (gh).')
app.add_typer(
    templates.app,
    name='template',
    help='Inspect, register, and use project templates (copier or cruft).',
)
app.add_typer(brew.app, name='brew', help='Manage developer tools (brew).')
app.add_typer(mise.app, name='mise', help='Keep mise configuration aligned across profiles.')
app.add_typer(
    devbox.app,
    name='devbox',
    help='Provision the development container (dnf in distrobox).',
)
app.add_typer(system.app, name='system', help='System health checks.')
app.add_typer(config.app, name='config', help='Manage athome configuration.')

# Top-level shortcut aliases
app.command(name='create', help='Scaffold a project (alias: template use <target> create).')(
    templates.create
)
app.command(name='templates', help='List templates (alias: template list).')(
    templates.list_templates
)
app.command(name='setup', help='Create a starter config.toml (alias: config init).')(config.init)

# Top-level command spanning brew + mise across every configured profile
app.command(name='cleanup', help='Reconcile installed brew/mise state against every profile.')(
    cleanup.cleanup
)

# One-time new-machine setup: register + clone personal, merge its athome.toml
app.command(name='bootstrap', help='One-time setup: register + clone personal, merge athome.toml.')(
    bootstrap.bootstrap
)

if __name__ == '__main__':  # pragma: no cover
    app()

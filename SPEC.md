# Athome

Agnostic developer environment orchestrator by Dev'Oc Collectif.

## Specification

Athome (pronounce "at home"), is a Developer Experience Optimisation tool for ones that need to centralize
multiple mechanisme, Athome does not provide functionnality itself, it's an agregate of interface to help
users in workspace management.

Athome have different interface :
- Profiles and files managers : provide interface to manage shared files, configuration tool and initialization script. Backend: `chezmoi`.
- Workspace managers : provide interface to manage git hosting and repositories by syncing and creating them. Backend: `gh`.
- Templates managers: Template help user to create new project based on a scaffold project, Athome uses `copier` and `cookiecutter` (via `cruft`) as backends, selectable per template.
- Brew managers : provide interface to control developer tools. Backend: `brew`.

Each interface has exactly one backend today, and athome does not carry a plugin/registry system to
select between backends at runtime — each CLI command module instantiates its one concrete manager
directly. Profile (chezmoi) and brew have no separate abstract base class anymore: with only one
implementation each, the interface contract lives directly on the concrete manager. Workspace (`gh`)
keeps its `WorkspaceManager` ABC since a second backend (e.g. gitlab) is a real near-term possibility;
`TemplateEngine` keeps its ABC too, since it already has two implementations (copier, cruft).

`mise` is handled separately from the tool-manager interface above: athome does not install or pin
tool versions through mise (that stays mise's own job). Instead athome reads every profile's mise
`conf.d` fragments to keep versions aligned across profiles (`athome mise check`) and to feed the
combined-cleanup flow (`athome cleanup`) — see below.

> A realistic configuration, covering all sections:
```toml
[profiles]
personal = "https://github.com/user/chezuser"
work = { source = "https://github.com/org/dotfiles-work", loads = ["personal"] }

[templates]
self-python-template = { source = "https://github.com/user/python-template", manager = "copier" }
self-zola-template = "https://github.com/user/zola-template"  # Default: `copier`
work-cookiecutter-template = { source = "https://github.com/org/uv-template", manager = "cruft" }

[workspace]
destination = "~/workspace"   # default clone destination

[workspace.owners]
user = { source = "https://github.com/user" }

[workspace.repos]  # extra repos not fully covered by an owner group
open-source = "https://github.com/open/source"

[brew]
perso-packages = { manifest = "~/.config/athome/Brewfile" }
```

### Managers

Managers are interfaces to other tools; each concrete manager MUST define a way to fallback if the
required tool is not installed or can't be used. A function handles that, based on class attributes:

- `fallback_require_tool` : display an error message that explains which tool is not installed and how to install it. Called automatically on manager instantiation.
- `REQUIRES` (attribute) : List of `RequireInstalled`.
- `RequireInstalled` (storage object) : a simple object with 2 properties: `tool`, `install_link`.

### Profiles

Profile offer a way to be initialized, synced, and applied easily, independently of the target tool.

The interface provide many entry point:
- `init` : Clone the remote dotfiles repository for a profile without applying.
- `is_initialized` : Return True if the source directory for a profile has been set up.
- `sync` : Pull change and apply them.
- `apply` : Apply locally staged managed files to the filesystem.
- `add` : Begin tracking *path* under *profile* (exposed on the CLI as `athome profile track`, since
  `athome profile add` is reserved for registering a new profile in config.toml — see below).
- `diff` : Print a diff of pending changes for *profile*.
- `status` : Print the current status of managed files for *profile*.

`athome profile apply-all` applies every configured profile unconditionally, in the order they appear
in `config.toml` — no diffing against a previous state, no backup, no unapply. This assumes purely
additive chezmoi profiles (nothing is ever removed by applying one); athome carries no state file and
no active-profile-stack concept.

### Template

Template centralizes multiple templating projects by exposing 3 methods:
- `create` : Scaffold a new project from *template_url* into *destination*. Accepts optional
  *data* (answer overrides) and *trust* (allow the template's declared tasks/hooks to run — maps
  to copier's `unsafe`; has no effect on cruft/cookiecutter, whose hooks always run unconditionally
  when present, so it is accepted and silently ignored rather than treated as an error).
- `update` : Update an existing project in *destination* to the latest template. Accepts the same
  optional *data* and *trust*.
- `is_initialized` : Return True if *destination* has already been scaffolded by this engine
  (copier: presence of `.copier-answers.yml`; cruft: presence of `.cruft.json`).

`athome template use <target> <create|sync|update> [destination]` is the CLI entry point —
`template`/`project` are one merged group. *target* is a template name from `[templates]` in
config.toml, or a direct git URL when not found there. The manager/engine is resolved from the
named template's config entry for all three actions — there is no `--manager` flag. `sync` is
idempotent create-or-update: it calls `is_initialized` on *destination* first and dispatches to
`create` or `update` accordingly. `--data key=value` (repeatable) forwards answer overrides to the
engine. `--trust` forwards to copier's `unsafe=True`; it is a no-op for the cruft engine. `athome
create <target> [destination]` remains a top-level shortcut for
`athome template use <target> create [destination]`.

### Workspace

Workspace help to manage git hosting and repository :
- `list_repos` : List repositories, optionally filtered by *owner* handle.
- `clone` : Clone *repo_url* into *destination* (defaults to current directory).
- `sync` : Clone or pull all repositories belonging to *owner_url* into *destination*.
- `create_repo` : Create a new remote repository named *name*.

`athome repo` exposes all four as a single command group (`list`/`clone`/`create` are ad hoc; `sync`
is the config-driven bulk operation over `[workspace.owners]` / `[workspace.repos]`).

### Brew

Expose methods to manage tool:

- `sync` : Install/sync *tools*, from the manifest.
- `upgrade` : Upgrade *tools* to their latest versions.
- `use` : Pin *tool* to *version* locally (or globally when *global_scope* is True).
- `list_tools` : Print all currently installed tools and their active versions.
- `doctor` : Run backend self-diagnostics and report any missing prerequisites.

### Mise alignment and cleanup

Every configured chezmoi profile may carry two kinds of fragment directories under its source tree,
mirroring the same "directory of fragments per profile" convention:

- `dot_config/brew/file.d/<context>.Brewfile[.tmpl]` — brew packages for that profile.
- `dot_config/mise/conf.d/<context>.toml` — mise tool versions for that profile.

`athome mise check` reads every profile's mise fragments and reports any tool pinned to a different
version across profiles (report-only, no auto-rewrite).

`athome cleanup` reconciles installed state against every configured profile's declared packages,
for both backends at once:
- Brew: aggregates every profile's Brewfile fragments (whether or not that profile is currently
  applied) into one combined manifest and runs `brew bundle cleanup` against it once.
- Mise: runs `mise prune` directly — mise already resolves every currently applied profile's
  conf.d fragment on its own, so no aggregation is needed on athome's side.

Both sides are non-destructive by default (list-only); `--force` opts into actually removing things.
`--skip-brew` / `--skip-mise` run just one side.

## Implementation Constraints (Python MVP)

- **Type Hinting**: 100% strict type hinting required.
- **Interfaces**: A manager inherits from `abc.ABC` only when its domain has more than one real
  implementation (today: `TemplateEngine`, `WorkspaceManager`); single-implementation domains fold
  the contract directly onto the concrete manager, which inherits `BaseManager` directly.
- **CLI Framework**: Use `typer` (no pure `argparse`).
- **Configuration**: Use `tomllib` to parse the configuration.
- **Code organisation**: Use semantic decomposition, inheritance and composition. Each CLI command module instantiates its one concrete manager directly — no dynamic plugin/registry indirection.
- **DX**: Use tox for CI task, Just for cmd execution, prek is used for pre-commit hooks, uv and direnv to manage environnement .

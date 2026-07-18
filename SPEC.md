# Athome

Agnostic developer environment orchestrator by Dev'Oc Collectif.

## Specification

Athome (pronounce "at home"), is a Developer Experience Optimisation tool for ones that need to centralize
multiple mechanisme, Athome does not provide functionnality itself, it's an agregate of interface to help
users in workspace management.

Athome have different interface :
- Profiles and files managers : provide interface to manage shared files, configuration tool and initialization script. The default manager is `chezmoi`
- Workspace managers : provide interface to manage git hosting and repositories by syncing and creatre them. the default manager is `gh`.
- Templates managers: Template help user to create new project base on a scaffold project, Athome use `copier` and `cookiecutter` (with `cruft`) as defaults.
- Tool managers : provide interface to controle different tool managers. The defaults are `mise` and `brew`.
- Env managers : provide interface to manage environement variable and runtime contexte. the defaults are `mise` and `direnv`.

For each type of interface, many of them can exist simultaneously, provide high management mechanisme, for example:

- A user have it's own project host to github, and use `cookiecutter` template, for it's own tool management, it use `brew` and `direnv` for context. dotfiles are managed by `chezmoi`
- The same user is employed in an enterprise, that use `gitlab` for hosting, `copier` for the templates, for env and tool `mise` is used. dotfiles are managed by `dotter`

> This user need a full configuration to setup each project :
```toml
[profiles]
personal = "https://github.com/user/chezuser"  # Default `chezmoi`
ec2 = { source = "https://github.com/user/ec2", manager = "chezmoi" }
self-work = { source = "https://github.com/org/user-setup", manager = "dotter" }
setup-remote = { source = "https://github.com/org/vm-setup", manager = "dotter", backup = "work-env", loads = ["base", "self-work"] }

[profiles.backup]
default-backup = "base"  # Name of the first backup made before any profile application.
profile-backup = "{profile.name}"  # a configurable or fix name for each profile, before applying a new profile the current one is backuped is this format.

[templates]
self-python-template = { source = "https://github.com/user/python-template", manager = "copier" }
self-zola-template = "https://github.com/user/python-template"  # Default: `copier`
work-python-template = {source = "https://github.com/org/uv-template", manager = "cookiecutter" }

[workspace]
destination = "~/workspace"   # default clone destination for all providers

[workspace.owners]
user = { source = "https://github.com/user", manager = "gh" }
work = { source = "https://selfhosted.com/org", manager = "gitlab" }

[workspace.repos]  # extra repos management not fully managed from the org/users
open-source = "https://github.com/open/source"  # Default: `gh`
contract-superversion = { source = "https://github.com/open/source", manager = "gitlab" }

[tools]
perso-packages = { manager = "brew", manifest = "~/.config/athome/Brewfile" }
work-packages = { manager = "mise", manifest = "~/.config/athome/work-mise.toml" }

[env]
work = { engine = "mise", shell = "zsh" }
user = {engine = "direnv", shell = "zsh"}

[env.variables]
ATHOME_ENV = "production"
```

### Managers

Managers are interface to other tools, each of them Must define a way to fallback if the require tool is not installed or can't be used.
A function is define to handle that and is based on property:

- `fallback_require_tool` : display a error message that explain which tool is not installed and how to installed it
- `REQUIRES` (attribute) : List of `RequireInstalled`.
- `RequireInstalled` (storage object) : a simple object with 2 properties: `tool`, `install_link`.

Managers are registry to a ManagersRegistry for each type of them, they are loaded from a specific pluging system based on entry point definition.

### Profiles

Profile offer a way to be loaded, backuped or apply easily, independently of the target tool.

The interface provide many entry point:
- `_init` : A private method to setup locally the profile (cloning for example, and/or `chezmoi init`).
- `sync` : Pull change and apply them.
- `apply` : Apply locally staged managed files to the filesystem.
- `add` : Begin tracking *path* under *profile*.
- `diff` : Print a diff of pending changes for *profile*.
- `status` : Print the current status of managed files for *profile*.
- `list_pending_paths` : Return target paths that will be modified or deleted by the next apply.
- `backup` : How to build the backup folder, the backup folder is made before applying new profile.
- `unapply` : execute a clean and strategic clean of the file that are not more activate (based on the `loads` key of the profile object)

The Athome profile orchestrator manages the state of the active profile stack.

During a switch:
1. It calculates the difference between the active stack and the target stack (`loads`).
2. For each profile removed from the stack, it calls `unapply()`.
3. For each profile added to the stack, it calls `apply()`.
4. A profile's `unapply()` method should only target files or file alterations that it itself introduced, without impacting the underlying profiles.

### Template

Template centralize multiple templating project by exposing 2 methods:
- `create` : Scaffold a new project from *template_url* into *destination*.
- `update` : Update an existing project in *destination* to the latest template. If Not Implemented du to the engine, the error is properly catch and return to the user.

### Workspace

Workspace help to manage git hosting and repository :
- `list_repos` : List repositories, optionally filtered by *owner* handle.
- `clone` : Clone *repo_url* into *destination* (defaults to current directory).
- `sync` : Clone or pull all repositories belonging to *owner_url* into *destination*.
- `create_repo` : Create a new remote repository named *name*.

### Tools

Expose methods to manage tool:

- `sync` : Install/sync *tools*, from the manifest.
- `upgrade` : Upgrade *tools* to their latest versions.
- `use` : Pin *tool* to *version* locally (or globally when *global_scope* is True).
- `list_tools` : Print all currently installed tools and their active versions.
- `doctor` : Run backend self-diagnostics and report any missing prerequisites.

### Env

Load Athome environement variable or setup context loader :

- `load` : Expose Athome Environement variable by environment loading evaluation.
- `activate` : Setup Context loader.

## Implementation Constraints (Python MVP)

- **Type Hinting**: 100% strict type hinting required.
- **Interfaces**: Every manager MUST inherit from `abc.ABC`.
- **CLI Framework**: Use `typer` (no pure `argparse`).
- **Configuration**: Use `tomllib` to parse the configuration.
- **Code organisation**: Use semantic decomposition, inheritance and composition. Apply strict design pattern to make high evolution system, based on registry for example.
- **DX**: Use tox for CI task, Just for cmd execution, prek is used for pre-commit hooks, uv and direnv to manage environnement .

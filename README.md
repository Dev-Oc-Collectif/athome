# athome

`athome` keeps your dotfiles, dev tools, and language runtimes in sync across every machine and
every "hat" you wear — personal, work, whatever else — from one `config.toml`.

It wraps three tools you may already use and gives them a shared, profile-aware config so you stop
running the same `chezmoi apply` / `brew bundle` / `mise install` dance by hand on each machine:

- **[chezmoi](https://chezmoi.io/)** — your dotfiles, as one or more named **profiles** (e.g.
  `personal`, `work`), each isolated with its own source/config/state so they don't collide.
- **[brew](https://brew.sh/)** — the CLI tools and apps each profile expects, declared as Brewfile
  fragments, installed and kept in sync.
- **[mise](https://mise.jdx.dev/)** — the language/tool runtime versions each profile pins, checked
  for drift across profiles.

On top of that, `athome` can also scaffold new projects from templates (`copier`/`cruft`) and
bulk-clone/sync your repositories (`gh`) — so `athome` is the one command you run on a fresh machine,
or after pulling profile updates, to bring everything back to a known, stateful configuration.

## Why

If you juggle multiple contexts (a personal setup and a work setup, or several client setups) you
end up maintaining several copies of "how I like a machine to look" — dotfiles here, a Brewfile
there, a tool-versions file somewhere else — and re-applying them by hand whenever something
changes. `athome` centralizes that as one config file and one set of commands, so applying,
updating, or reconciling a profile is always the same command regardless of which profile it is.

## Installation

```sh
pip install .
# or, from source, for development:
uv sync --dev
```

Requires the backends you intend to use: `chezmoi`, `brew`, `mise`, `gh`. Check what's missing with:

```sh
athome system doctor
```

## Quickstart

1. Create `~/.config/athome/config.toml` — interactively:

   ```sh
   athome config init
   ```

   or by hand, following [`config.example.toml`](config.example.toml):

   ```toml
   [profiles]
   personal = "https://github.com/user/chezuser"
   work = "https://github.com/org/dotfiles-work"

   [brew]
   perso-packages = { manifest = "~/.config/athome/Brewfile" }
   ```

2. Bring a profile onto the machine:

   ```sh
   athome profile init work      # clone the dotfiles repo, don't apply yet
   athome profile apply work     # apply managed files to the filesystem
   ```

   Or do both, for every configured profile, in one shot on a fresh machine:

   ```sh
   athome profile apply-all
   ```

3. Day to day, pull in upstream changes and re-apply:

   ```sh
   athome profile sync work
   ```

4. Keep tool versions honest across profiles, and clean up what's no longer declared anywhere:

   ```sh
   athome mise check     # report tools pinned to different versions across profiles
   athome cleanup        # dry-run reconciliation of installed brew/mise state; --force to act
   ```

## Command reference

### `athome profile` — dotfiles (chezmoi)

| Command | Does |
|---|---|
| `profile add <name> <source>` | Register a profile in config.toml |
| `profile init <name>` | Clone the profile's dotfiles repo (no apply) |
| `profile apply <name>` | Apply locally staged files to the filesystem |
| `profile sync <name>` | Pull latest changes and apply them |
| `profile apply-all` | Init (if needed) + apply every configured profile |
| `profile track <name> <path>` | Start tracking a file/dir under a profile |
| `profile diff <name>` / `profile status <name>` | Inspect pending changes |
| `profile list` | List configured profiles |

### `athome brew` — dev tools

| Command | Does |
|---|---|
| `brew add <name> <manifest>` | Register a Brewfile entry |
| `brew sync [name]` | Install from a manifest (all, if name omitted) |
| `brew upgrade [name] [--tool]` | Upgrade tools in an entry |
| `brew list [name]` | List entries, or installed tools within one |

### `athome mise` — runtime versions

| Command | Does |
|---|---|
| `mise check` | Report tools pinned to different versions across profiles |

### `athome cleanup` — reconcile installed state

Aggregates every profile's Brewfile fragments and runs `brew bundle cleanup` once, and runs
`mise prune`. Dry-run by default — pass `--force` to actually remove things, `--skip-brew` /
`--skip-mise` to run just one side.

### `athome template` — project scaffolding (copier / cruft)

| Command | Does |
|---|---|
| `template add <name> <source> [--manager]` | Register a template |
| `template use <target> create [dest]` | Scaffold a new project |
| `template use <target> update [dest]` | Update an existing project to the latest template |
| `template use <target> sync [dest]` | Create if new, update if already scaffolded |
| `template list` | List configured templates |
| `create <target> [dest]` | Shortcut for `template use <target> create` |

### `athome repo` — git hosting (gh)

| Command | Does |
|---|---|
| `repo add-owner <name> <source>` / `repo add-repo <name> <source>` | Register in config.toml |
| `repo create <name> [--public]` | Create a remote repository |
| `repo clone <url> [dest]` | Clone a single repository |
| `repo list [owner]` | List remote repositories |
| `repo sync [--dest]` | Clone/pull every repo under `[workspace.owners]` / `[workspace.repos]` |

### `athome config` / `athome system`

| Command | Does |
|---|---|
| `config init` (alias: `athome setup`) | Interactively create config.toml |
| `config show` | Print the current config |
| `config edit` | Open config.toml in `$EDITOR` |
| `system doctor` | Check that required backends are on PATH |

See [`SPEC.md`](SPEC.md) for how `athome` is built internally.

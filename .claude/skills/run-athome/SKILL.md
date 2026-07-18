---
name: run-athome
description: run, start, test, screenshot, smoke-test, or verify the athome CLI — build the venv, exercise commands, check exit codes and output
---

`athome` is a Typer-based Python CLI. It has no server or GUI — the agent path is
`bash .claude/skills/run-athome/smoke.sh`, a smoke script that exercises all
commands, controls config via `HOME` override, and asserts exit codes + output.

## Prerequisites

Python 3.14+ and `uv` must be on PATH (both present in this container).
No system packages needed beyond what `uv` provisions.

## Build / install

```bash
uv sync --dev
```

Creates `.venv/` with all runtime and dev dependencies.

## Run — agent path

```bash
bash .claude/skills/run-athome/smoke.sh
```

Runs 23 assertions across help output, graceful empty-config messages,
fixture-config output, error exit codes, and `system doctor`.
Exits 0 on full pass, 1 on any failure — suitable as a CI step.
Every assertion runs through the **installed console script** (`.venv/bin/athome`),
not `python -m ...` — this is what actually catches a broken entry point.

**What the smoke script covers:**

| Category | What is tested |
|---|---|
| Structure | `--help` for root + every sub-command |
| Empty config | `profile list`, `template list` print graceful "none configured" messages, exit 0 |
| Fixture config | `profile list` / `template list` return names and URLs from a temp `config.toml` |
| Error path | `profile sync <nonexistent>` exits 1 with a readable message |
| System doctor | Prints `✓`/`✗` per tool, tolerates missing tools on CI |

**Config fixture** is written to a temp `$FAKEHOME/.config/athome/config.toml`
and injected via `HOME=$FAKEHOME`. Cleaned up on exit.

**Invoking the CLI directly** (outside the smoke script):

```bash
.venv/bin/athome --help
.venv/bin/athome system doctor
HOME=/tmp/fake .venv/bin/athome profile list   # no config → graceful empty
```

Once installed via `uv tool install .` (or `pip install -e .`):

```bash
athome --help
```

## Run — human path

```bash
uv run athome --help
```

## Test suite

```bash
uv run pytest -q
```

## Gotchas

- **`$PYTHON` word-split trap.** Never assign a multi-word command to a variable and
  use it in `"$@"`. Use a shell function: `athome() { .venv/bin/athome "$@"; }`.
- **`((N++))` under `set -e`.** When `N=0`, `((0))` returns exit 1, aborting the script.
  Use `N=$((N + 1))` instead.
- **Config path is `$HOME`-relative.** `load_config()` resolves to
  `Path.home() / '.config' / 'athome' / 'config.toml'`. Override by passing
  a `Path` to `load_config(path=...)` directly, or point the whole `HOME` env
  var at a temp directory — the latter is how the smoke script isolates tests.
- **Entry point is `athome`, not `devoc`.** An older iteration used `devoc`;
  `pyproject.toml` was updated. `devoc` is gone.

"""Profile stack orchestrator — manages activation and deactivation of profile sets."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

from athome.definitions.config import STATE_PATH
from athome.definitions.config import ProfileConfig


@dataclass
class AthomeState:
    """Persisted runtime state for athome."""

    active_profiles: list[str] = field(default_factory=list)


def load_state(path: Path = STATE_PATH) -> AthomeState:
    """Read the active profile stack from *path*, returning an empty state when absent."""
    if not path.exists():
        return AthomeState()
    with path.open('rb') as fh:
        raw = tomllib.load(fh)
    return AthomeState(active_profiles=list(raw.get('active_profiles', [])))


def save_state(state: AthomeState, path: Path = STATE_PATH) -> None:
    """Persist *state* to *path* as TOML."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ['active_profiles = [']
    lines += [f'  {name!r},' for name in state.active_profiles]
    lines += [']', '']
    path.write_text('\n'.join(lines))


def resolve_stack(
    profile_name: str,
    all_profiles: dict[str, ProfileConfig],
    _visited: set[str] | None = None,
) -> list[str]:
    """Return topologically ordered profile names for *profile_name* and all its loads.

    Profiles listed in ``loads`` are resolved recursively and placed before
    the profile that depends on them (depth-first). Cycles are silently broken
    by skipping already-visited nodes.
    """
    if _visited is None:
        _visited = set()
    if profile_name in _visited:
        return []
    _visited.add(profile_name)

    result: list[str] = []
    profile = all_profiles.get(profile_name)
    if profile is not None:
        for dep in profile.loads:
            result.extend(resolve_stack(dep, all_profiles, _visited))
    result.append(profile_name)
    return result


def compute_switch(
    old_stack: list[str],
    new_stack: list[str],
) -> tuple[list[str], list[str], set[str]]:
    """Return *(to_unapply, to_apply, remaining)* for a stack transition.

    *to_unapply* is ordered in reverse so that the most-derived profile is
    unapplied first. *to_apply* preserves the topological order of *new_stack*.
    """
    old_set = set(old_stack)
    new_set = set(new_stack)
    remaining = old_set & new_set
    to_unapply = [p for p in reversed(old_stack) if p not in new_set]
    to_apply = [p for p in new_stack if p not in old_set]
    return to_unapply, to_apply, remaining

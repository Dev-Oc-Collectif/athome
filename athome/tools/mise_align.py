"""Cross-profile mise configuration alignment check.

athome doesn't install or pin tools through mise (that stays mise's own job) — it
only reads each profile's ``dot_config/mise/conf.d/*.toml`` fragments to flag a
tool that's pinned to a different version in different profiles, so drift is
visible before it causes a surprise on whichever machine loads both.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from athome.definitions.config import ProfileConfig
from athome.definitions.config import profile_source_root

MISE_CONFD_GLOB = 'dot_config/mise/conf.d/*.toml'


@dataclass(frozen=True)
class ToolDrift:
    """A tool pinned to more than one distinct version across profiles."""

    tool: str
    versions: dict[str, str]  # profile name -> normalized version


def _normalize_version(value: Any) -> str:
    """Reduce a mise tool-spec value to a comparable string."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return str(value.get('version', value))
    if isinstance(value, list):
        return ','.join(sorted(_normalize_version(v) for v in value))
    return str(value)


def _read_tools(fragment: Path) -> dict[str, str]:
    """Return {tool: normalized version} declared in a single conf.d fragment."""
    with fragment.open('rb') as fh:
        raw = tomllib.load(fh)
    tools_raw: dict[str, Any] = raw.get('tools', {})
    return {name: _normalize_version(value) for name, value in tools_raw.items()}


def collect_tool_versions(
    profiles: dict[str, ProfileConfig],
) -> dict[str, dict[str, str]]:
    """Build {tool: {profile_name: version}} across every profile's mise fragments."""
    tool_versions: dict[str, dict[str, str]] = {}
    for profile in profiles.values():
        source = profile_source_root(profile)
        for fragment in sorted(source.glob(MISE_CONFD_GLOB)):
            for tool, version in _read_tools(fragment).items():
                tool_versions.setdefault(tool, {})[profile.name] = version
    return tool_versions


def find_drift(profiles: dict[str, ProfileConfig]) -> list[ToolDrift]:
    """Return one ToolDrift per tool pinned to more than one distinct version."""
    tool_versions = collect_tool_versions(profiles)
    return [
        ToolDrift(tool=tool, versions=versions)
        for tool, versions in sorted(tool_versions.items())
        if len(set(versions.values())) > 1
    ]

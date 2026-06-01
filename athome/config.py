"""Configuration engine for athome — parses ~/.config/athome/config.toml."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any

CONFIG_PATH: Path = Path.home() / '.config' / 'athome' / 'config.toml'
PROFILES_SOURCE_BASE: Path = Path.home() / '.local' / 'share' / 'athome' / 'profiles'
PROFILES_CONFIG_BASE: Path = Path.home() / '.config' / 'athome' / 'profiles'


@dataclass(frozen=True)
class ProfileConfig:
    """A named dotfile profile backed by a git repository.

    *destination* overrides the default XDG source directory for chezmoi.
    When absent, athome derives the path from PROFILES_SOURCE_BASE.
    """

    name: str
    source: str
    destination: Path | None = None


@dataclass(frozen=True)
class GitConfig:
    """Remote git owners, individual repositories, and workspace settings."""

    workspace: Path = field(default_factory=lambda: Path.home() / 'workspace')
    owners: dict[str, dict[str, str]] = field(default_factory=dict)
    repositories: dict[str, dict[str, str]] = field(default_factory=dict)


@dataclass(frozen=True)
class AthomeConfig:
    """Root configuration object parsed from config.toml."""

    profiles: dict[str, ProfileConfig] = field(default_factory=dict)
    templates: dict[str, str] = field(default_factory=dict)
    git: GitConfig = field(default_factory=GitConfig)
    managers: dict[str, str] = field(default_factory=dict)


def _parse_profile(name: str, value: Any) -> ProfileConfig:
    """Parse a single profile entry — accepts a bare URL string or an inline table."""
    if isinstance(value, str):
        return ProfileConfig(name=name, source=value)
    destination_raw: str | None = value.get('destination')
    return ProfileConfig(
        name=name,
        source=value['source'],
        destination=Path(destination_raw).expanduser() if destination_raw else None,
    )


def load_profiles(profiles_raw: dict[str, Any]) -> dict[str, ProfileConfig]:
    """Parse the [profiles] section; values may be plain strings or inline tables."""
    return {name: _parse_profile(name, value) for name, value in profiles_raw.items()}


def load_templates(template: dict[str, str]) -> dict[str, str]:
    """Parse the [templates] section and return a name→URL mapping."""
    return template


def load_git(git_raw: dict[str, Any]) -> GitConfig:
    """Parse the [git] section into a typed GitConfig."""
    workspace_raw: str | None = git_raw.get('workspace')
    workspace = Path(workspace_raw).expanduser() if workspace_raw else Path.home() / 'workspace'
    return GitConfig(
        workspace=workspace,
        owners=git_raw.get('owners', {}),
        repositories=git_raw.get('repositories', {}),
    )


def load_config(path: Path = CONFIG_PATH) -> AthomeConfig:
    """Parse config.toml and return a typed AthomeConfig.

    Returns an empty config when the file is absent — callers must not assume
    any key exists without checking.
    """
    if not path.exists():
        return AthomeConfig()

    with path.open('rb') as fh:
        raw: Any = tomllib.load(fh)

    return AthomeConfig(
        profiles=load_profiles(raw.get('profiles', {})),
        templates=load_templates(raw.get('templates', {})),
        git=load_git(raw.get('git', {})),
        managers=raw.get('managers', {}),
    )


def profile_source_path(profile: ProfileConfig) -> Path:
    """Chezmoi --source path for *profile*, respecting a custom destination."""
    if profile.destination is not None:
        return profile.destination
    return PROFILES_SOURCE_BASE / profile.name


def profile_config_path(profile_name: str) -> Path:
    """Chezmoi --config path for a given profile (always XDG-derived)."""
    return PROFILES_CONFIG_BASE / f'{profile_name}.toml'


def profile_state_path(profile_name: str) -> Path:
    """Chezmoi --state path for a given profile (always XDG-derived)."""
    return PROFILES_CONFIG_BASE / f'{profile_name}-state.db'

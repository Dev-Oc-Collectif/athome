"""Configuration engine for athome — parses ~/.config/athome/config.toml."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from dataclasses import field
from functools import cache
from pathlib import Path
from typing import Any

CONFIG_PATH: Path = Path.home() / '.config' / 'athome' / 'config.toml'
PROFILES_SOURCE_BASE: Path = Path.home() / '.local' / 'share' / 'athome' / 'profiles'
PROFILES_CONFIG_BASE: Path = Path.home() / '.config' / 'athome' / 'profiles'


@dataclass(frozen=True)
class ProfileConfig:
    """A named dotfile profile backed by a git repository, managed by chezmoi.

    *loads* lists other profile names that must be active alongside this one,
    forming a dependency stack.
    """

    name: str
    source: str
    destination: Path | None = None
    loads: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class OwnerConfig:
    """A named git owner (org or user account) in the [workspace.owners] section."""

    source: str


@dataclass(frozen=True)
class RepoConfig:
    """A named individual repository in the [workspace.repos] section."""

    source: str


@dataclass(frozen=True)
class DestinationConfig:
    """A target destination folder define in the [workspace] section."""

    target: Path = field(default_factory=lambda: Path.home() / 'workspace')


@dataclass(frozen=True)
class WorkspaceConfig:
    """Remote git owners, individual repositories, and workspace settings."""

    destination: DestinationConfig = field(default_factory=DestinationConfig)
    owners: dict[str, OwnerConfig] = field(default_factory=dict)
    repos: dict[str, RepoConfig] = field(default_factory=dict)


@dataclass(frozen=True)
class TemplateConfig:
    """A named project template in the [templates] section."""

    source: str
    manager: str = 'copier'


@dataclass(frozen=True)
class BrewEntryConfig:
    """A named Brewfile manifest entry in the [brew] section (backend: brew)."""

    manifest: Path


@dataclass(frozen=True)
class AthomeConfig:
    """Root configuration object parsed from config.toml."""

    profiles: dict[str, ProfileConfig] = field(default_factory=dict)
    templates: dict[str, TemplateConfig] = field(default_factory=dict)
    workspace: WorkspaceConfig = field(default_factory=WorkspaceConfig)
    brew: dict[str, BrewEntryConfig] = field(default_factory=dict)


def _parse_profile(name: str, value: Any) -> ProfileConfig:
    """Parse a single profile entry — accepts a bare URL string or an inline table."""
    if isinstance(value, str):
        return ProfileConfig(name=name, source=value)
    destination_raw: str | None = value.get('destination')
    return ProfileConfig(
        name=name,
        source=value['source'],
        destination=Path(destination_raw).expanduser() if destination_raw else None,
        loads=list(value.get('loads', [])),
    )


def load_profiles(profiles_raw: dict[str, Any]) -> dict[str, ProfileConfig]:
    """Parse the [profiles] section into a name→ProfileConfig mapping."""
    return {name: _parse_profile(name, value) for name, value in profiles_raw.items()}


def _parse_template(value: Any) -> TemplateConfig:
    """Parse a template entry — accepts a bare URL string or an inline table."""
    if isinstance(value, str):
        return TemplateConfig(source=value)
    return TemplateConfig(source=value['source'], manager=value.get('manager', 'copier'))


def load_templates(templates_raw: dict[str, Any]) -> dict[str, TemplateConfig]:
    """Parse the [templates] section into a name→TemplateConfig mapping."""
    return {name: _parse_template(value) for name, value in templates_raw.items()}


def _parse_owner(value: Any) -> OwnerConfig:
    """Parse a workspace owner entry — accepts a bare URL string or an inline table."""
    if isinstance(value, str):
        return OwnerConfig(source=value)
    return OwnerConfig(source=value['source'])


def _parse_repo(value: Any) -> RepoConfig:
    """Parse a workspace repo entry — accepts a bare URL string or an inline table."""
    if isinstance(value, str):
        return RepoConfig(source=value)
    return RepoConfig(source=value['source'])


def _parse_workspace_destionation(value: Any) -> DestinationConfig:
    if isinstance(value, str):
        destination_target = Path(value)
    elif isinstance(value, dict):
        destination_target = Path(value['target'])
    else:
        destination_target = Path.home() / 'workspace'
    return DestinationConfig(target=destination_target.expanduser())


def load_workspace(workspace_raw: dict[str, Any]) -> WorkspaceConfig:
    """Parse the [workspace] section into a typed WorkspaceConfig."""
    destination_raw: str | dict[str, str] | None = workspace_raw.get('destination')
    owners_raw: dict[str, Any] = workspace_raw.get('owners', {})
    repos_raw: dict[str, Any] = workspace_raw.get('repos', {})
    return WorkspaceConfig(
        destination=_parse_workspace_destionation(destination_raw),
        owners={name: _parse_owner(v) for name, v in owners_raw.items()},
        repos={name: _parse_repo(v) for name, v in repos_raw.items()},
    )


def _parse_brew_entry(value: Any) -> BrewEntryConfig:
    """Parse a brew entry — accepts a bare manifest path string or an inline table."""
    if isinstance(value, str):
        return BrewEntryConfig(manifest=Path(value).expanduser())
    return BrewEntryConfig(manifest=Path(value['manifest']).expanduser())


def load_brew(brew_raw: dict[str, Any]) -> dict[str, BrewEntryConfig]:
    """Parse the [brew] section."""
    return {name: _parse_brew_entry(value) for name, value in brew_raw.items()}


@cache
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
        workspace=load_workspace(raw.get('workspace', {})),
        brew=load_brew(raw.get('brew', {})),
    )


def profile_source_path(profile: ProfileConfig) -> Path:
    """Source directory for *profile*, respecting a custom destination."""
    if profile.destination is not None:
        return profile.destination
    return PROFILES_SOURCE_BASE / profile.name


def profile_config_path(profile_name: str) -> Path:
    """Backend config path for a given profile (always XDG-derived)."""
    return PROFILES_CONFIG_BASE / f'{profile_name}.toml'


def profile_state_path(profile_name: str) -> Path:
    """Backend state path for a given profile (always XDG-derived)."""
    return PROFILES_CONFIG_BASE / f'{profile_name}-state.db'

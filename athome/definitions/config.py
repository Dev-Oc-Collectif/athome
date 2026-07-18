"""Configuration engine for athome — parses ~/.config/athome/config.toml."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from dataclasses import field
from functools import cache
from pathlib import Path
from typing import Any

CONFIG_PATH: Path = Path.home() / '.config' / 'athome' / 'config.toml'
STATE_PATH: Path = Path.home() / '.config' / 'athome' / 'state.toml'
PROFILES_SOURCE_BASE: Path = Path.home() / '.local' / 'share' / 'athome' / 'profiles'
PROFILES_CONFIG_BASE: Path = Path.home() / '.config' / 'athome' / 'profiles'


@dataclass(frozen=True)
class ProfileConfig:
    """A named dotfile profile backed by a git repository.

    *manager* selects which SharedFileManager backend handles this profile
    (default: "chezmoi"). *loads* lists other profile names that must be
    active alongside this one, forming a dependency stack.
    """

    name: str
    source: str
    manager: str = 'chezmoi'
    destination: Path | None = None
    backup: str | None = None
    loads: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ProfileBackupConfig:
    """Backup naming policy applied before any profile switch."""

    default_backup: str = 'base'
    profile_backup: str = '{profile.name}'


@dataclass(frozen=True)
class OwnerConfig:
    """A named git owner (org or user account) in the [workspace.owners] section."""

    source: str
    manager: str = 'gh'


@dataclass(frozen=True)
class RepoConfig:
    """A named individual repository in the [workspace.repos] section."""

    source: str
    manager: str = 'gh'


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
class ToolEntryConfig:
    """A named tool manifest entry in the [tools] section."""

    manager: str
    manifest: Path


@dataclass(frozen=True)
class EnvEntryConfig:
    """A named env context entry in the [env] section."""

    engine: str
    shell: str


@dataclass(frozen=True)
class EnvConfig:
    """All env contexts and globally declared variables."""

    entries: dict[str, EnvEntryConfig] = field(default_factory=dict)
    variables: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class AthomeConfig:
    """Root configuration object parsed from config.toml."""

    profiles: dict[str, ProfileConfig] = field(default_factory=dict)
    profile_backup: ProfileBackupConfig = field(default_factory=ProfileBackupConfig)
    templates: dict[str, TemplateConfig] = field(default_factory=dict)
    workspace: WorkspaceConfig = field(default_factory=WorkspaceConfig)
    tools: dict[str, ToolEntryConfig] = field(default_factory=dict)
    env: EnvConfig = field(default_factory=EnvConfig)
    managers: dict[str, str] = field(default_factory=dict)


def _parse_profile(name: str, value: Any) -> ProfileConfig:
    """Parse a single profile entry — accepts a bare URL string or an inline table."""
    if isinstance(value, str):
        return ProfileConfig(name=name, source=value)
    destination_raw: str | None = value.get('destination')
    return ProfileConfig(
        name=name,
        source=value['source'],
        manager=value.get('manager', 'chezmoi'),
        destination=Path(destination_raw).expanduser() if destination_raw else None,
        backup=value.get('backup'),
        loads=list(value.get('loads', [])),
    )


def _parse_profile_backup(raw: dict[str, Any]) -> ProfileBackupConfig:
    return ProfileBackupConfig(
        default_backup=raw.get('default-backup', 'base'),
        profile_backup=raw.get('profile-backup', '{profile.name}'),
    )


def load_profiles(
    profiles_raw: dict[str, Any],
) -> tuple[dict[str, ProfileConfig], ProfileBackupConfig]:
    """Parse the [profiles] section.

    The special ``backup`` sub-key is extracted as a ProfileBackupConfig;
    all other keys are treated as profile entries.
    """
    backup_cfg = _parse_profile_backup(profiles_raw.get('backup', {}))
    profiles = {
        name: _parse_profile(name, value)
        for name, value in profiles_raw.items()
        if name != 'backup'
    }
    return profiles, backup_cfg


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
    return OwnerConfig(source=value['source'], manager=value.get('manager', 'gh'))


def _parse_repo(value: Any) -> RepoConfig:
    """Parse a workspace repo entry — accepts a bare URL string or an inline table."""
    if isinstance(value, str):
        return RepoConfig(source=value)
    return RepoConfig(source=value['source'], manager=value.get('manager', 'gh'))


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


def _parse_tool_entry(value: Any) -> ToolEntryConfig:
    return ToolEntryConfig(
        manager=value['manager'],
        manifest=Path(value['manifest']).expanduser(),
    )


def load_tools(tools_raw: dict[str, Any]) -> dict[str, ToolEntryConfig]:
    """Parse the [tools] section."""
    return {name: _parse_tool_entry(value) for name, value in tools_raw.items()}


def _parse_env_entry(value: Any) -> EnvEntryConfig:
    return EnvEntryConfig(engine=value['engine'], shell=value['shell'])  # nosec


def load_env(env_raw: dict[str, Any]) -> EnvConfig:
    """Parse the [env] section, separating the special ``variables`` sub-key."""
    variables: dict[str, str] = env_raw.get('variables', {})
    entries = {
        name: _parse_env_entry(value) for name, value in env_raw.items() if name != 'variables'
    }
    return EnvConfig(entries=entries, variables=variables)


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

    profiles, profile_backup = load_profiles(raw.get('profiles', {}))
    return AthomeConfig(
        profiles=profiles,
        profile_backup=profile_backup,
        templates=load_templates(raw.get('templates', {})),
        workspace=load_workspace(raw.get('workspace', {})),
        tools=load_tools(raw.get('tools', {})),
        env=load_env(raw.get('env', {})),
        managers=raw.get('managers', {}),
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

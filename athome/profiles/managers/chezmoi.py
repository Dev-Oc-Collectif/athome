"""SharedFileManager implementation backed by chezmoi."""

from __future__ import annotations

import subprocess  # nosec
from pathlib import Path

from athome.profiles.backup import backup_files
from athome.definitions.config import ProfileConfig
from athome.definitions.config import profile_config_path
from athome.definitions.config import profile_source_path
from athome.definitions.config import profile_state_path
from athome.definitions.managers.base import RequireInstalled
from athome.definitions.managers.profile import ProfileManager

_INSTALL_HINT = 'https://chezmoi.io/'


class ChezmoiManager(ProfileManager):
    """Chezmoi-backed dotfile manager with per-profile path isolation.

    Each profile gets its own --source / --config / --state flags so that a
    single machine can host multiple chezmoi profiles without them interfering
    with each other or with a pre-existing system-level chezmoi installation.
    """

    REQUIRES = [RequireInstalled('chezmoi', _INSTALL_HINT)]

    def _profile_flags(self, profile: ProfileConfig) -> list[str]:
        return [
            f'--source={profile_source_path(profile)}',
            f'--config={profile_config_path(profile.name)}',
            f'--persistent-state={profile_state_path(profile.name)}',
        ]

    def _run(self, profile: ProfileConfig, *args: str) -> None:
        cmd: list[str] = ['chezmoi', *self._profile_flags(profile), *args]
        subprocess.run(cmd, check=True)  # noqa: S603 # nosec

    def is_initialized(self, profile: ProfileConfig) -> bool:
        """Return True if the profile source directory exists."""
        return profile_source_path(profile).exists()

    def init(self, profile: ProfileConfig) -> None:
        """Clone the remote repo into the profile source directory without applying."""
        profile_config_path(profile.name).parent.mkdir(parents=True, exist_ok=True)
        profile_source_path(profile).parent.mkdir(parents=True, exist_ok=True)
        self._run(profile, 'init', profile.source, '--apply=false')

    def sync(self, profile: ProfileConfig) -> None:
        """Pull and apply the latest remote changes for *profile*."""
        self._run(profile, 'update')

    def apply(self, profile: ProfileConfig) -> None:
        """Apply staged managed files to the filesystem for *profile*."""
        self._run(profile, 'apply')

    def add(self, profile: ProfileConfig, path: Path) -> None:
        """Start tracking *path* under *profile*."""
        self._run(profile, 'add', str(path))

    def diff(self, profile: ProfileConfig) -> None:
        """Show pending changes for *profile*."""
        self._run(profile, 'diff')

    def status(self, profile: ProfileConfig) -> None:
        """Show managed files status for *profile*."""
        self._run(profile, 'status')

    def list_pending_paths(self, profile: ProfileConfig) -> list[Path]:
        """Return target paths that currently exist and will be touched by the next apply."""
        result = subprocess.run(  # noqa: S603 # nosec
            ['chezmoi', *self._profile_flags(profile), 'status'],
            capture_output=True,
            text=True,
            check=False,
        )
        home = Path.home()
        paths: list[Path] = []
        for line in result.stdout.splitlines():
            if len(line) < 3:  # noqa: PLR2004
                continue
            path_str = line[3:].strip()
            if not path_str:
                continue
            path = Path(path_str) if Path(path_str).is_absolute() else home / path_str
            if path.exists() and path.is_file():
                paths.append(path)
        return paths

    def _list_managed_paths(self, profile: ProfileConfig) -> list[Path]:
        """Return all paths currently managed by *profile* that exist on disk."""
        result = subprocess.run(  # noqa: S603 # nosec
            ['chezmoi', *self._profile_flags(profile), 'managed', '--path-style=absolute'],
            capture_output=True,
            text=True,
            check=False,
        )
        home = Path.home()
        paths: list[Path] = []
        for line in result.stdout.splitlines():
            path_str = line.strip()
            if not path_str:
                continue
            path = Path(path_str) if Path(path_str).is_absolute() else home / path_str
            if path.exists() and path.is_file():
                paths.append(path)
        return paths

    def backup(self, profile: ProfileConfig, backup_dir: Path) -> int:
        """Snapshot files that will be touched by the next apply into *backup_dir*.

        Returns the count of files actually copied.
        """
        paths = self.list_pending_paths(profile)
        return backup_files(paths, backup_dir)

    def unapply(self, profile: ProfileConfig, safe_paths: frozenset[Path]) -> None:
        """Remove files introduced by *profile* that are not in *safe_paths*."""
        for path in self._list_managed_paths(profile):
            if path not in safe_paths:
                path.unlink(missing_ok=True)

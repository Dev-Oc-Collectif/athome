"""SharedFileManager implementation backed by chezmoi."""

from __future__ import annotations

import shutil
import subprocess  # nosec
from pathlib import Path

from athome.config import ProfileConfig
from athome.config import profile_config_path
from athome.config import profile_source_path
from athome.config import profile_state_path
from athome.exceptions import ToolNotFoundError
from athome.interfaces.shared_file_manager import SharedFileManager

_INSTALL_HINT = 'https://chezmoi.io/'


class ChezmoidManager(SharedFileManager):
    """Chezmoi-backed dotfile manager with per-profile path isolation.

    Each profile gets its own --source / --config / --state flags so that a
    single machine can host multiple chezmoi profiles without them interfering
    with each other or with a pre-existing system-level chezmoi installation.
    """

    def _profile_flags(self, profile: ProfileConfig) -> list[str]:
        return [
            f'--source={profile_source_path(profile)}',
            f'--config={profile_config_path(profile.name)}',
            f'--state={profile_state_path(profile.name)}',
        ]

    def _run(self, profile: ProfileConfig, *args: str) -> None:
        if not shutil.which('chezmoi'):
            raise ToolNotFoundError('chezmoi', _INSTALL_HINT)
        cmd: list[str] = ['chezmoi', *self._profile_flags(profile), *args]
        subprocess.run(cmd, check=True)  # noqa: S603 # nosec

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

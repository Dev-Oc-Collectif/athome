"""Chezmoi-backed dotfile manager."""

from __future__ import annotations

import subprocess  # nosec
from pathlib import Path

from athome.definitions.config import ProfileConfig
from athome.definitions.config import profile_config_path
from athome.definitions.config import profile_source_path
from athome.definitions.config import profile_state_path
from athome.definitions.managers.base import BaseManager
from athome.definitions.managers.base import RequireInstalled

_INSTALL_HINT = 'https://chezmoi.io/'


class ChezmoiManager(BaseManager):
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

    def render_template(self, profile: ProfileConfig, template_path: Path) -> str:
        """Render *template_path* (a .tmpl file) through *profile*'s chezmoi templating."""
        cmd = ['chezmoi', *self._profile_flags(profile), 'execute-template']
        result = subprocess.run(  # noqa: S603 # nosec
            cmd,
            input=template_path.read_text(),
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout

    def is_initialized(self, profile: ProfileConfig) -> bool:
        """Return True if the profile source directory is a real git checkout.

        A bare existence check isn't enough: a failed `chezmoi init` (e.g. a
        broken clone, or an interrupted config-template render) can leave an
        empty source directory behind, which would otherwise be mistaken for
        a completed init on every later command.
        """
        return (profile_source_path(profile) / '.git').exists()

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

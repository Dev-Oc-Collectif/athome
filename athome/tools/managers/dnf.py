"""dnf-backed developer tool manager, running inside a distrobox dev box.

An immutable host (Fedora Silverblue/Kinoite and friends) deliberately ships no
development userspace: no `cc`, no `/usr/include`, no `-devel` packages, and no
way to add them without layering. The dev box is that userspace, and `dnf` is
its native package manager — so declaring a package here means writing its name
in a fragment, never hand-rolling a wrapper.
"""

from __future__ import annotations

import subprocess  # nosec

from athome.definitions.managers.base import BaseManager
from athome.definitions.managers.base import RequireInstalled

_INSTALL_HINT = 'https://distrobox.it/'

# Packages the image itself shipped. `dnf repoquery --userinstalled` cannot tell
# them apart from ours — everything baked in at image build time is "user
# installed" too — so reconciling against it directly would propose removing the
# whole base image. We snapshot that set once, before the first install, and
# treat anything added afterwards as ours. It lives inside the box so its
# lifetime matches the box's: destroy the box and the baseline goes with it.
_BASELINE_PATH = '/var/lib/athome/baseline'


class DnfManager(BaseManager):
    """Developer tool manager backed by `dnf` inside a distrobox container."""

    REQUIRES = [RequireInstalled('distrobox', _INSTALL_HINT)]

    def _box(self, box: str, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        self.fallback_require_tool()
        return subprocess.run(  # noqa: S603 # nosec
            ['distrobox', 'enter', box, '--', *args],
            check=check,
            capture_output=True,
            text=True,
        )

    def _user_installed(self, box: str) -> set[str]:
        # The trailing newline is load-bearing: without it dnf concatenates every
        # package name into a single blob, and the parsed set is one giant entry.
        result = self._box(box, 'dnf', 'repoquery', '--userinstalled', '--qf', '%{name}\n')
        return {line.strip() for line in result.stdout.splitlines() if line.strip()}

    def _write_baseline(self, box: str, baseline: set[str]) -> None:
        self.fallback_require_tool()
        subprocess.run(  # noqa: S603 # nosec
            ['distrobox', 'enter', box, '--', 'sudo', 'tee', _BASELINE_PATH],
            input='\n'.join(sorted(baseline)),
            check=True,
            capture_output=True,
            text=True,
        )

    def ensure_baseline(self, box: str) -> set[str]:
        """Return the image's own package set, recording it on first call.

        Called before the first install so the snapshot captures the image as
        shipped. Once written it is never rewritten: a later call would fold
        our own packages into the baseline and make them unremovable.
        """
        existing = self._box(box, 'cat', _BASELINE_PATH, check=False)
        if existing.returncode == 0 and existing.stdout.strip():
            return {line.strip() for line in existing.stdout.splitlines() if line.strip()}

        baseline = self._user_installed(box)
        self._box(box, 'sudo', 'mkdir', '-p', _BASELINE_PATH.rsplit('/', 1)[0])
        self._write_baseline(box, baseline)
        return baseline

    def sync(self, box: str, packages: list[str]) -> None:
        """Install every declared package into *box*."""
        if not packages:
            return
        self.ensure_baseline(box)
        self._box(box, 'sudo', 'dnf', 'install', '-y', *packages)

    def removable(self, box: str, declared: set[str]) -> list[str]:
        """Return packages we installed into *box* that nothing declares any more."""
        baseline = self.ensure_baseline(box)
        return sorted(self._user_installed(box) - baseline - declared)

    def cleanup(self, box: str, declared: set[str], *, force: bool = False) -> list[str]:
        """Remove undeclared packages from *box*; list them without removing unless *force*."""
        extra = self.removable(box, declared)
        if extra and force:
            self._box(box, 'sudo', 'dnf', 'remove', '-y', *extra)
        return extra

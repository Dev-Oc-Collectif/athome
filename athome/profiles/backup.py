"""Backup utilities — snapshot managed files before applying changes."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path


def default_backup_name(profile_name: str) -> str:
    """Return a deterministic, timestamped backup folder name for *profile_name*."""
    now = datetime.now()
    return f'backup-before-apply-{profile_name}_{now:%Y-%m-%d_%H-%M-%S}'


def backup_files(paths: list[Path], backup_dir: Path) -> int:
    """Copy each existing *paths* entry into *backup_dir*, preserving home-relative layout.

    Files outside HOME are stored flat (by filename only).
    Returns the count of files actually copied.
    """
    home = Path.home()
    count = 0
    for path in paths:
        if not path.exists():
            continue
        try:
            rel = path.relative_to(home)
        except ValueError:
            rel = Path(path.name)
        dest = backup_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        count += 1
    return count

"""Shared fixtures for the athome test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from athome.config import AthomeConfig
from athome.config import GitConfig
from athome.config import ProfileConfig


@pytest.fixture
def full_config() -> AthomeConfig:
    """A fully populated AthomeConfig covering all sections."""
    return AthomeConfig(
        profiles={
            'work': ProfileConfig(name='work', source='https://github.com/org/dotfiles-work'),
            'personal': ProfileConfig(name='personal', source='https://github.com/user/dotfiles'),
        },
        templates={
            'python': 'https://github.com/Dev-Oc-Collectif/python-template',
            'zola': 'https://github.com/Dev-Oc-Collectif/zola-template',
        },
        git=GitConfig(
            owners={'gh': {'org': 'https://github.com/my-org'}},
            repositories={'gh': {'dotfiles': 'https://github.com/user/dotfiles'}},
        ),
    )


@pytest.fixture
def empty_config() -> AthomeConfig:
    """A config with no entries — represents a missing or empty config.toml."""
    return AthomeConfig()


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    """Write a complete config.toml to tmp_path and return the path."""
    path = tmp_path / 'config.toml'
    path.write_bytes(
        b'[profiles]\n'
        b'work     = "https://github.com/org/dotfiles-work"\n'
        b'personal = "https://github.com/user/dotfiles"\n'
        b'\n'
        b'[templates]\n'
        b'python = "https://github.com/Dev-Oc-Collectif/python-template"\n'
        b'zola   = "https://github.com/Dev-Oc-Collectif/zola-template"\n'
        b'\n'
        b'[git.owners.gh]\n'
        b'org = "https://github.com/my-org"\n'
        b'\n'
        b'[git.repositories.gh]\n'
        b'dotfiles = "https://github.com/user/dotfiles"\n'
    )
    return path

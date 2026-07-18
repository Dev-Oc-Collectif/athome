"""Shared fixtures for the athome test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from athome.definitions.config import AthomeConfig
from athome.definitions.config import OwnerConfig
from athome.definitions.config import ProfileConfig
from athome.definitions.config import RepoConfig
from athome.definitions.config import TemplateConfig
from athome.definitions.config import WorkspaceConfig


@pytest.fixture
def full_config() -> AthomeConfig:
    """A fully populated AthomeConfig covering all sections."""
    return AthomeConfig(
        profiles={
            'work': ProfileConfig(name='work', source='https://github.com/org/dotfiles-work'),
            'personal': ProfileConfig(name='personal', source='https://github.com/user/dotfiles'),
        },
        templates={
            'python': TemplateConfig(source='https://github.com/Dev-Oc-Collectif/python-template'),
            'zola': TemplateConfig(source='https://github.com/Dev-Oc-Collectif/zola-template'),
        },
        workspace=WorkspaceConfig(
            owners={'my-org': OwnerConfig(source='https://github.com/my-org', manager='gh')},
            repos={'dotfiles': RepoConfig(source='https://github.com/user/dotfiles', manager='gh')},
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
        b'[workspace.owners]\n'
        b'my-org = {source = "https://github.com/my-org", manager = "gh"}\n'
        b'\n'
        b'[workspace.repos]\n'
        b'dotfiles = "https://github.com/user/dotfiles"\n'
    )
    return path

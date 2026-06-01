"""Tests for the ABC interface contracts."""

from __future__ import annotations

from pathlib import Path

import pytest

from athome.config import ProfileConfig
from athome.interfaces.env_manager import EnvManager
from athome.interfaces.git_manager import GitManager
from athome.interfaces.shared_file_manager import SharedFileManager
from athome.interfaces.template_engine import TemplateEngine


class TestSharedFileManagerIsAbstract:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            SharedFileManager()  # type: ignore[abstract]

    def test_partial_implementation_raises(self) -> None:
        class Partial(SharedFileManager):
            def sync(self, profile: ProfileConfig) -> None: ...

        with pytest.raises(TypeError):
            Partial()  # type: ignore[abstract]

    def test_full_implementation_instantiates(self) -> None:
        class Full(SharedFileManager):
            def sync(self, profile: ProfileConfig) -> None: ...
            def apply(self, profile: ProfileConfig) -> None: ...
            def add(self, profile: ProfileConfig, path: Path) -> None: ...
            def diff(self, profile: ProfileConfig) -> None: ...
            def status(self, profile: ProfileConfig) -> None: ...

        assert isinstance(Full(), SharedFileManager)


class TestTemplateEngineIsAbstract:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            TemplateEngine()  # type: ignore[abstract]

    def test_full_implementation_instantiates(self) -> None:
        class Full(TemplateEngine):
            def create(self, template_url: str, destination: object) -> None: ...
            def update(self, destination: object) -> None: ...

        assert isinstance(Full(), TemplateEngine)


class TestEnvManagerIsAbstract:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            EnvManager()  # type: ignore[abstract]

    def test_full_implementation_instantiates(self) -> None:
        class Full(EnvManager):
            def install(self, tool: str, version: object = None) -> None: ...
            def upgrade(self, tool: object = None) -> None: ...
            def use(self, tool: str, version: str, *, global_scope: bool = False) -> None: ...
            def list_tools(self) -> None: ...
            def doctor(self) -> None: ...

        assert isinstance(Full(), EnvManager)


class TestGitManagerIsAbstract:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            GitManager()  # type: ignore[abstract]

    def test_full_implementation_instantiates(self) -> None:
        class Full(GitManager):
            def list_repos(self, owner: object = None) -> None: ...
            def clone(self, repo_url: str, destination: object = None) -> None: ...
            def sync_workspace(self, owner_url: str, destination: object) -> None: ...
            def create_repo(self, name: str, *, private: bool = True) -> None: ...

        assert isinstance(Full(), GitManager)

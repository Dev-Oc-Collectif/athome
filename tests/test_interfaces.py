"""Tests for the ABC interface contracts."""

from __future__ import annotations

from pathlib import Path

import pytest

from athome.definitions.config import ProfileConfig
from athome.definitions.managers.context import ContextManager
from athome.definitions.managers.workspace import WorkspaceManager
from athome.definitions.managers.profile import ProfileManager
from athome.definitions.managers.template import TemplateEngine
from athome.definitions.managers.tool import ToolManager


class TestSharedFileManagerIsAbstract:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            ProfileManager()  # type: ignore[abstract]

    def test_partial_implementation_raises(self) -> None:
        class Partial(ProfileManager):
            def sync(self, profile: ProfileConfig) -> None: ...

        with pytest.raises(TypeError):
            Partial()  # type: ignore[abstract]

    def test_full_implementation_instantiates(self) -> None:  # noqa: C901
        class Full(ProfileManager):
            def init(self, profile: ProfileConfig) -> None: ...
            def is_initialized(self, profile: ProfileConfig) -> bool:
                return True

            def sync(self, profile: ProfileConfig) -> None: ...
            def apply(self, profile: ProfileConfig) -> None: ...
            def add(self, profile: ProfileConfig, path: Path) -> None: ...
            def diff(self, profile: ProfileConfig) -> None: ...
            def status(self, profile: ProfileConfig) -> None: ...
            def list_pending_paths(self, profile: ProfileConfig) -> list[Path]:
                return []

            def backup(self, profile: ProfileConfig, backup_dir: Path) -> int:
                return 0

            def unapply(self, profile: ProfileConfig, safe_paths: frozenset[Path]) -> None: ...

        assert isinstance(Full(), ProfileManager)


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
            ContextManager()  # type: ignore[abstract]

    def test_full_implementation_instantiates(self) -> None:
        class Full(ContextManager):
            def load(self) -> None: ...
            def activate(self, shell: str = 'bash') -> None: ...

        assert isinstance(Full(), ContextManager)


class TestToolManagerIsAbstract:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            ToolManager()  # type: ignore[abstract]

    def test_full_implementation_instantiates(self) -> None:
        class Full(ToolManager):
            def sync(self, manifest: Path) -> None: ...
            def upgrade(self, tool: object = None) -> None: ...
            def use(self, tool: str, version: str, *, global_scope: bool = False) -> None: ...
            def list_tools(self) -> None: ...
            def doctor(self) -> None: ...

        assert isinstance(Full(), ToolManager)


class TestGitManagerIsAbstract:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            WorkspaceManager()  # type: ignore[abstract]

    def test_full_implementation_instantiates(self) -> None:
        class Full(WorkspaceManager):
            def list_repos(self, owner: object = None) -> None: ...
            def clone(self, repo_url: str, destination: object = None) -> None: ...
            def sync(self, owner_url: str, destination: object) -> None: ...
            def create_repo(self, name: str, *, private: bool = True) -> None: ...

        assert isinstance(Full(), WorkspaceManager)

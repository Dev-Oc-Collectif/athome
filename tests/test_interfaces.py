"""Tests for the ABC interface contracts."""

from __future__ import annotations

import pytest

from athome.definitions.managers.template import TemplateEngine
from athome.definitions.managers.workspace import WorkspaceManager


class TestTemplateEngineIsAbstract:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            TemplateEngine()  # type: ignore[abstract]

    def test_full_implementation_instantiates(self) -> None:
        class Full(TemplateEngine):
            def create(
                self,
                template_url: str,
                destination: object,
                *,
                data: object = None,
                trust: bool = False,
            ) -> None: ...
            def update(
                self, destination: object, *, data: object = None, trust: bool = False
            ) -> None: ...
            def is_initialized(self, destination: object) -> bool:
                return False

        assert isinstance(Full(), TemplateEngine)


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

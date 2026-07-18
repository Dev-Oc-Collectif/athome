"""Base primitives shared by all athome manager implementations."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from typing import ClassVar

from athome.exceptions import ToolNotFoundError


@dataclass(frozen=True)
class RequireInstalled:
    """Describes an external tool that a manager depends on."""

    tool: str
    install_link: str


class BaseManager:
    """Mixin that provides the standard tool-requirement contract.

    Concrete managers declare ``REQUIRES`` at class level; the harness and
    commands call ``fallback_require_tool()`` once before delegating work.
    """

    REQUIRES: ClassVar[list[RequireInstalled]] = []

    def __init__(self) -> None:
        self.fallback_require_tool()

    def fallback_require_tool(self) -> None:
        """Raise ToolNotFoundError for the first missing tool in REQUIRES."""
        for req in self.REQUIRES:
            if not shutil.which(req.tool):
                raise ToolNotFoundError(req.tool, req.install_link)

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

    Concrete managers declare ``REQUIRES`` at class level. Construction never
    checks for the tool — managers are built eagerly at CLI module import
    time (see e.g. ``athome.cli.brew``), so raising here would mean simply
    importing athome's CLI fails on a machine missing *any* required tool,
    even for a command that never touches that manager. Instead, each
    manager calls ``fallback_require_tool()`` itself at its own subprocess
    choke point(s), right before actually shelling out.
    """

    REQUIRES: ClassVar[list[RequireInstalled]] = []

    def fallback_require_tool(self) -> None:
        """Raise ToolNotFoundError for the first missing tool in REQUIRES."""
        for req in self.REQUIRES:
            if not shutil.which(req.tool):
                raise ToolNotFoundError(req.tool, req.install_link)

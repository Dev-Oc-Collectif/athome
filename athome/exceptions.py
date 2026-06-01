"""Custom exceptions for athome."""

from __future__ import annotations

import click


class ToolNotFoundError(click.ClickException):
    """Raised when a required external CLI tool is not installed.

    Subclasses click.ClickException so that Typer/Click automatically
    displays a clean ``Error: …`` message and exits with code 1 — no
    try/except required in command code.
    """

    def __init__(self, tool: str, install_hint: str = '') -> None:
        self.tool = tool
        self.install_hint = install_hint
        message = f"Required tool '{tool}' is not installed."
        if install_hint:
            message += f' Install it from: {install_hint}'
        super().__init__(message)

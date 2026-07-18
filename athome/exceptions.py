"""Custom exceptions for athome."""

from __future__ import annotations
from typing import Sequence

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


class AthomeException(Exception):  # noqa: N818
    """Exception de base pour l'application Athome."""

    pass


class EntryNotFoundError(AthomeException):
    """Levée quand une clé (ex: 'work') n'existe pas dans le TOML."""

    def __init__(self, domain_label: str, name: str, defined_keys: list[str]):
        self.domain_label = domain_label
        self.name = name
        self.defined_keys = defined_keys
        super().__init__(f'{domain_label} entry "{name}" not found.')


class ManagerNotFoundError(AthomeException):
    """Levée quand le plugin/manager sous-jacent (ex: 'chezmoi') n'est pas dispo."""

    def __init__(self, domain_label: str, manager_name: str):
        self.domain_label = domain_label
        self.manager_name = manager_name
        super().__init__(f'No {domain_label.lower()} manager "{manager_name}" available.')


class ManagerDefinitionError(AthomeException):
    """Levée quand le manager sous-jacent est mal défini dans le TOML."""

    pass


class ManagerSourceCodeError(AthomeException):
    """Levée quand le manager sous-jacent est mal défini dans le code."""

    def __init__(self, param: str) -> None:
        super().__init__(f"Missing Parameter {param}")


class ManagerSourceCodeMissingError[T: AthomeException](ExceptionGroup):
    """Plop."""

    def __init__(self, missed: str, exceptions: Sequence[T]) -> None:
        super().__init__(f"Missing {missed} in Manager(s)", exceptions)

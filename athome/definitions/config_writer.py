"""Structured, format-preserving writer for config.toml.

Used exclusively by the `add` CLI commands (profile/template/owner/repo/brew).
Reads and writes via tomlkit so that existing comments, key ordering, and
formatting in the user's real config.toml survive an `add` untouched — the
plain string-building approach in cli/config.py's `init` is fine for creating
a config from scratch but would destroy that structure on an existing file.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

import tomlkit

from athome.definitions.config import CONFIG_PATH
from athome.exceptions import ConfigEntryExistsError

if TYPE_CHECKING:
    from tomlkit.items import InlineTable
    from tomlkit.items import Table


def _load_document(path: Path) -> tomlkit.TOMLDocument:
    if not path.exists():
        return tomlkit.document()
    return tomlkit.parse(path.read_text())


def _write_document(doc: tomlkit.TOMLDocument, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(tomlkit.dumps(doc))


def _get_or_create_table(doc: tomlkit.TOMLDocument, *segments: str) -> Table:
    node: Any = doc
    for segment in segments:
        if segment not in node:
            node[segment] = tomlkit.table()
        node = node[segment]
    return node


def _add_entry(
    path: Path,
    section: tuple[str, ...],
    name: str,
    value: str | InlineTable,
) -> None:
    doc = _load_document(path)
    table = _get_or_create_table(doc, *section)
    if name in table:
        raise ConfigEntryExistsError(name, '.'.join(section))
    table[name] = value
    _write_document(doc, path)


def add_profile(
    name: str,
    source: str,
    *,
    destination: str | None = None,
    loads: list[str] | None = None,
    path: Path = CONFIG_PATH,
) -> None:
    """Add a [profiles] entry — bare string when only *source* is given, else inline table."""
    if destination is None and not loads:
        _add_entry(path, ('profiles',), name, source)
        return
    entry = tomlkit.inline_table()
    entry['source'] = source
    if destination is not None:
        entry['destination'] = destination
    if loads:
        entry['loads'] = loads
    _add_entry(path, ('profiles',), name, entry)


def add_template(
    name: str,
    source: str,
    *,
    manager: str = 'copier',
    path: Path = CONFIG_PATH,
) -> None:
    """Add a [templates] entry — bare string when manager is the default ('copier')."""
    if manager == 'copier':
        _add_entry(path, ('templates',), name, source)
        return
    entry = tomlkit.inline_table()
    entry['source'] = source
    entry['manager'] = manager
    _add_entry(path, ('templates',), name, entry)


def add_owner(name: str, source: str, *, path: Path = CONFIG_PATH) -> None:
    """Add a [workspace.owners] entry."""
    _add_entry(path, ('workspace', 'owners'), name, source)


def add_repo(name: str, source: str, *, path: Path = CONFIG_PATH) -> None:
    """Add a [workspace.repos] entry."""
    _add_entry(path, ('workspace', 'repos'), name, source)


def add_brew_entry(name: str, manifest: str, *, path: Path = CONFIG_PATH) -> None:
    """Add a [brew] entry."""
    _add_entry(path, ('brew',), name, manifest)

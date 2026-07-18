"""Tests for athome.definitions.config_writer — format-preserving config.toml edits."""

from __future__ import annotations

from pathlib import Path

import pytest

from athome.definitions import config_writer
from athome.exceptions import ConfigEntryExistsError


class TestAddProfile:
    def test_bare_string_when_no_extra_fields(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        config_writer.add_profile('work', 'https://github.com/org/dots', path=p)
        content = p.read_text()
        assert 'work = "https://github.com/org/dots"' in content

    def test_inline_table_with_destination(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        config_writer.add_profile(
            'work', 'https://github.com/org/dots', destination='/custom/dest', path=p
        )
        content = p.read_text()
        assert 'destination = "/custom/dest"' in content

    def test_inline_table_with_loads(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        config_writer.add_profile('work', 'https://github.com/org/dots', loads=['base'], path=p)
        content = p.read_text()
        assert 'loads = ["base"]' in content

    def test_creates_profiles_section_from_scratch(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        config_writer.add_profile('work', 'https://github.com/org/dots', path=p)
        assert '[profiles]' in p.read_text()

    def test_duplicate_name_raises(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        config_writer.add_profile('work', 'https://github.com/org/dots', path=p)
        with pytest.raises(ConfigEntryExistsError):
            config_writer.add_profile('work', 'https://github.com/other/dots', path=p)


class TestAddTemplate:
    def test_bare_string_for_default_manager(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        config_writer.add_template('python', 'https://github.com/org/python-template', path=p)
        content = p.read_text()
        assert 'python = "https://github.com/org/python-template"' in content

    def test_inline_table_for_cruft_manager(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        config_writer.add_template(
            'zola', 'https://github.com/org/zola-template', manager='cruft', path=p
        )
        content = p.read_text()
        assert 'manager = "cruft"' in content

    def test_duplicate_name_raises(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        config_writer.add_template('python', 'https://github.com/org/python-template', path=p)
        with pytest.raises(ConfigEntryExistsError):
            config_writer.add_template('python', 'https://github.com/other/template', path=p)


class TestAddOwner:
    def test_creates_nested_workspace_owners_table(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_text('[workspace]\ndestination = "~/workspace"\n')
        config_writer.add_owner('myorg', 'https://github.com/myorg', path=p)
        content = p.read_text()
        assert '[workspace.owners]' in content
        assert 'myorg = "https://github.com/myorg"' in content

    def test_creates_workspace_section_from_scratch(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        config_writer.add_owner('myorg', 'https://github.com/myorg', path=p)
        assert '[workspace.owners]' in p.read_text()

    def test_duplicate_name_raises(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        config_writer.add_owner('myorg', 'https://github.com/myorg', path=p)
        with pytest.raises(ConfigEntryExistsError):
            config_writer.add_owner('myorg', 'https://github.com/other', path=p)


class TestAddRepo:
    def test_creates_nested_workspace_repos_table(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        config_writer.add_repo('dotfiles', 'https://github.com/user/dotfiles', path=p)
        content = p.read_text()
        assert '[workspace.repos]' in content
        assert 'dotfiles = "https://github.com/user/dotfiles"' in content

    def test_duplicate_name_raises(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        config_writer.add_repo('dotfiles', 'https://github.com/user/dotfiles', path=p)
        with pytest.raises(ConfigEntryExistsError):
            config_writer.add_repo('dotfiles', 'https://github.com/other/dotfiles', path=p)


class TestAddBrewEntry:
    def test_creates_brew_section_from_scratch(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        config_writer.add_brew_entry('work', '~/.config/brew/file.d/work.Brewfile', path=p)
        content = p.read_text()
        assert '[brew]' in content
        assert 'work = "~/.config/brew/file.d/work.Brewfile"' in content

    def test_duplicate_name_raises(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        config_writer.add_brew_entry('work', '~/Brewfile', path=p)
        with pytest.raises(ConfigEntryExistsError):
            config_writer.add_brew_entry('work', '~/OtherBrewfile', path=p)


class TestFormatPreservation:
    def test_preserves_header_and_inline_comments(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_text(
            '# athome configuration — ~/.config/athome/config.toml\n'
            '\n'
            '[profiles]\n'
            'work = "https://github.com/org/dots"  # main profile\n'
        )
        config_writer.add_profile('personal', 'https://github.com/user/dots', path=p)
        content = p.read_text()
        assert '# athome configuration — ~/.config/athome/config.toml' in content
        assert 'work = "https://github.com/org/dots"  # main profile' in content
        assert 'personal = "https://github.com/user/dots"' in content

    def test_unrelated_sections_untouched(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        original = (
            '[profiles]\n'
            'work = "https://github.com/org/dots"\n'
            '\n'
            '[templates]\n'
            'python = "https://github.com/org/python-template"\n'
            '\n'
            '[workspace.owners]\n'
            'myorg = "https://github.com/myorg"\n'
            '\n'
            '[brew]\n'
            'self = "~/Brewfile"\n'
        )
        p.write_text(original)
        config_writer.add_profile('personal', 'https://github.com/user/dots', path=p)
        content = p.read_text()
        assert 'python = "https://github.com/org/python-template"' in content
        assert 'myorg = "https://github.com/myorg"' in content
        assert 'self = "~/Brewfile"' in content

    def test_creates_file_when_absent(self, tmp_path: Path) -> None:
        p = tmp_path / 'nested' / 'config.toml'
        config_writer.add_profile('work', 'https://github.com/org/dots', path=p)
        assert p.exists()
        assert 'work = "https://github.com/org/dots"' in p.read_text()

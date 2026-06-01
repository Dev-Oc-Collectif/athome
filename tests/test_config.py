"""Tests for athome.config — configuration parser and path helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from athome.config import AthomeConfig
from athome.config import GitConfig
from athome.config import ProfileConfig
from athome.config import load_config
from athome.config import profile_config_path
from athome.config import profile_source_path
from athome.config import profile_state_path


class TestLoadConfigMissingFile:
    def test_returns_empty_config_when_file_absent(self, tmp_path: Path) -> None:
        result = load_config(tmp_path / 'nonexistent.toml')
        assert isinstance(result, AthomeConfig)

    def test_empty_config_has_no_profiles(self, tmp_path: Path) -> None:
        result = load_config(tmp_path / 'nonexistent.toml')
        assert result.profiles == {}

    def test_empty_config_has_no_templates(self, tmp_path: Path) -> None:
        result = load_config(tmp_path / 'nonexistent.toml')
        assert result.templates == {}

    def test_empty_config_has_empty_git(self, tmp_path: Path) -> None:
        result = load_config(tmp_path / 'nonexistent.toml')
        assert result.git.owners == {}
        assert result.git.repositories == {}


class TestLoadConfigEmptyToml:
    def test_empty_file_returns_empty_config(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_bytes(b'')
        result = load_config(p)
        assert result.profiles == {}
        assert result.templates == {}


class TestLoadConfigProfiles:
    def test_parses_profile_names(self, config_file: Path) -> None:
        result = load_config(config_file)
        assert set(result.profiles) == {'work', 'personal'}

    def test_profile_config_has_correct_name(self, config_file: Path) -> None:
        result = load_config(config_file)
        assert result.profiles['work'].name == 'work'

    def test_profile_config_has_correct_source(self, config_file: Path) -> None:
        result = load_config(config_file)
        assert result.profiles['work'].source == 'https://github.com/org/dotfiles-work'

    def test_all_profiles_parsed(self, config_file: Path) -> None:
        result = load_config(config_file)
        assert result.profiles['personal'].source == 'https://github.com/user/dotfiles'

    def test_profiles_section_only(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_bytes(b'[profiles]\ndev = "https://github.com/user/dotfiles-dev"\n')
        result = load_config(p)
        assert result.profiles['dev'].source == 'https://github.com/user/dotfiles-dev'
        assert result.templates == {}


class TestLoadConfigTemplates:
    def test_parses_template_names(self, config_file: Path) -> None:
        result = load_config(config_file)
        assert set(result.templates) == {'python', 'zola'}

    def test_template_url_values(self, config_file: Path) -> None:
        result = load_config(config_file)
        assert result.templates['python'] == 'https://github.com/Dev-Oc-Collectif/python-template'

    def test_templates_section_only(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_bytes(b'[templates]\nrust = "https://github.com/org/rust-template"\n')
        result = load_config(p)
        assert result.templates['rust'] == 'https://github.com/org/rust-template'
        assert result.profiles == {}


class TestLoadConfigGit:
    def test_parses_owners_providers(self, config_file: Path) -> None:
        result = load_config(config_file)
        assert 'gh' in result.git.owners

    def test_parses_owner_entries(self, config_file: Path) -> None:
        result = load_config(config_file)
        assert result.git.owners['gh']['org'] == 'https://github.com/my-org'

    def test_parses_repository_entries(self, config_file: Path) -> None:
        result = load_config(config_file)
        assert result.git.repositories['gh']['dotfiles'] == 'https://github.com/user/dotfiles'

    def test_git_section_only(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_bytes(b'[git.owners.github]\nmyorg = "https://github.com/myorg"\n')
        result = load_config(p)
        assert result.git.owners['github']['myorg'] == 'https://github.com/myorg'
        assert result.profiles == {}

    def test_missing_git_section_yields_empty_git(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_bytes(b'[profiles]\nwork = "https://github.com/org/dotfiles"\n')
        result = load_config(p)
        assert result.git.owners == {}
        assert result.git.repositories == {}

    def test_parses_workspace_from_git_section(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_bytes(b'[git]\nworkspace = "/custom/workspace"\n')
        result = load_config(p)
        assert result.git.workspace == Path('/custom/workspace')

    def test_workspace_default_when_absent(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_bytes(b'[git.owners.gh]\norg = "https://github.com/org"\n')
        result = load_config(p)
        assert result.git.workspace == Path.home() / 'workspace'


class TestLoadConfigRichProfileFormat:
    def test_inline_table_profile_parses_source(self, tmp_path: Path) -> None:
        dest = str(tmp_path / 'dots')
        p = tmp_path / 'config.toml'
        p.write_text(
            '[profiles]\npersonal = '
            f'{{source = "https://github.com/user/dots", destination = "{dest}"}}\n'
        )
        result = load_config(p)
        assert result.profiles['personal'].source == 'https://github.com/user/dots'

    def test_inline_table_profile_parses_destination(self, tmp_path: Path) -> None:
        dest = tmp_path / 'dots'
        p = tmp_path / 'config.toml'
        p.write_text(
            '[profiles]\npersonal = '
            f'{{source = "https://github.com/user/dots", destination = "{dest}"}}\n'
        )
        result = load_config(p)
        assert result.profiles['personal'].destination == dest

    def test_string_profile_has_no_destination(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_bytes(b'[profiles]\nwork = "https://github.com/org/dotfiles"\n')
        result = load_config(p)
        assert result.profiles['work'].destination is None

    def test_mixed_formats_coexist(self, tmp_path: Path) -> None:
        dest = tmp_path / 'dots'
        p = tmp_path / 'config.toml'
        p.write_text(
            '[profiles]\n'
            'work = "https://github.com/org/dotfiles-work"\n'
            'personal = '
            f'{{source = "https://github.com/user/dots", destination = "{dest}"}}\n'
        )
        result = load_config(p)
        assert result.profiles['work'].destination is None
        assert result.profiles['personal'].destination == dest


class TestDataclasses:
    def test_profile_config_is_frozen(self) -> None:
        p = ProfileConfig(name='x', source='url')
        with pytest.raises(AttributeError):
            p.name = 'y'  # type: ignore[misc] # ty: ignore[invalid-assignment]

    def test_git_config_defaults(self) -> None:
        g = GitConfig()
        assert g.owners == {}
        assert g.repositories == {}
        assert g.workspace == Path.home() / 'workspace'

    def test_athome_config_defaults(self) -> None:
        c = AthomeConfig()
        assert c.profiles == {}
        assert c.templates == {}
        assert isinstance(c.git, GitConfig)
        assert c.managers == {}


_P = ProfileConfig(name='myprofile', source='url')
_PX = ProfileConfig(name='x', source='url')
_PWORK = ProfileConfig(name='work', source='url')
_PPERSONAL = ProfileConfig(name='personal', source='url')


class TestPathHelpers:
    def test_profile_source_path_contains_profile_name(self) -> None:
        p = profile_source_path(_P)
        assert p.name == 'myprofile'
        assert 'profiles' in str(p)

    def test_profile_source_path_respects_custom_destination(self) -> None:
        custom = Path('/custom/dest')
        profile = ProfileConfig(name='myprofile', source='url', destination=custom)
        assert profile_source_path(profile) == custom

    def test_profile_config_path_is_toml(self) -> None:
        p = profile_config_path('myprofile')
        assert p.suffix == '.toml'
        assert p.stem == 'myprofile'

    def test_profile_state_path_is_db(self) -> None:
        p = profile_state_path('myprofile')
        assert p.name == 'myprofile-state.db'

    def test_path_helpers_are_absolute(self) -> None:
        assert profile_source_path(_PX).is_absolute()
        assert profile_config_path('x').is_absolute()
        assert profile_state_path('x').is_absolute()

    def test_different_profiles_yield_different_paths(self) -> None:
        assert profile_source_path(_PWORK) != profile_source_path(_PPERSONAL)
        assert profile_config_path('work') != profile_config_path('personal')
        assert profile_state_path('work') != profile_state_path('personal')

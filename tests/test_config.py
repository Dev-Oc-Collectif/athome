"""Tests for athome.config — configuration parser and path helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from athome.definitions.config import AthomeConfig
from athome.definitions.config import EnvConfig
from athome.definitions.config import ProfileBackupConfig
from athome.definitions.config import ProfileConfig
from athome.definitions.config import WorkspaceConfig
from athome.definitions.config import load_config
from athome.definitions.config import profile_config_path
from athome.definitions.config import profile_source_path
from athome.definitions.config import profile_state_path


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

    def test_empty_config_has_empty_workspace(self, tmp_path: Path) -> None:
        result = load_config(tmp_path / 'nonexistent.toml')
        assert result.workspace.owners == {}
        assert result.workspace.repos == {}


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

    def test_profile_default_manager_is_chezmoi(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_bytes(b'[profiles]\nwork = "https://github.com/org/dotfiles"\n')
        result = load_config(p)
        assert result.profiles['work'].manager == 'chezmoi'

    def test_profile_inline_table_manager_field(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_text(
            '[profiles]\nwork = {source = "https://github.com/org/dots", manager = "dotter"}\n'
        )
        result = load_config(p)
        assert result.profiles['work'].manager == 'dotter'

    def test_profile_loads_field(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_text(
            '[profiles]\n'
            'base = "https://github.com/user/base"\n'
            'work = {source = "https://github.com/org/dots", loads = ["base"]}\n'
        )
        result = load_config(p)
        assert result.profiles['work'].loads == ['base']

    def test_profile_backup_field(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_text(
            '[profiles]\nwork = {source = "https://github.com/org/dots", backup = "my-backup"}\n'
        )
        result = load_config(p)
        assert result.profiles['work'].backup == 'my-backup'

    def test_profiles_backup_subsection_not_treated_as_profile(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_text(
            '[profiles]\n'
            'work = "https://github.com/org/dots"\n'
            '\n'
            '[profiles.backup]\n'
            'default-backup = "base"\n'
        )
        result = load_config(p)
        assert 'backup' not in result.profiles
        assert result.profile_backup.default_backup == 'base'

    def test_profiles_backup_default_values(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_bytes(b'[profiles]\nwork = "https://github.com/org/dots"\n')
        result = load_config(p)
        assert result.profile_backup.default_backup == 'base'
        assert result.profile_backup.profile_backup == '{profile.name}'


class TestLoadConfigTemplates:
    def test_parses_template_names(self, config_file: Path) -> None:
        result = load_config(config_file)
        assert set(result.templates) == {'python', 'zola'}

    def test_template_source_value(self, config_file: Path) -> None:
        result = load_config(config_file)
        assert (
            result.templates['python'].source
            == 'https://github.com/Dev-Oc-Collectif/python-template'
        )

    def test_template_default_manager(self, config_file: Path) -> None:
        result = load_config(config_file)
        assert result.templates['python'].manager == 'copier'

    def test_template_explicit_manager(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_text(
            '[templates]\nrust = '
            '{source = "https://github.com/org/rust-template", manager = "cruft"}\n'
        )
        result = load_config(p)
        assert result.templates['rust'].manager == 'cruft'

    def test_templates_section_only(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_bytes(b'[templates]\nrust = "https://github.com/org/rust-template"\n')
        result = load_config(p)
        assert result.templates['rust'].source == 'https://github.com/org/rust-template'
        assert result.profiles == {}


class TestLoadConfigWorkspace:
    def test_parses_owner_names(self, config_file: Path) -> None:
        result = load_config(config_file)
        assert 'my-org' in result.workspace.owners

    def test_parses_owner_source(self, config_file: Path) -> None:
        result = load_config(config_file)
        assert result.workspace.owners['my-org'].source == 'https://github.com/my-org'

    def test_parses_owner_manager(self, config_file: Path) -> None:
        result = load_config(config_file)
        assert result.workspace.owners['my-org'].manager == 'gh'

    def test_parses_repo_entries(self, config_file: Path) -> None:
        result = load_config(config_file)
        assert result.workspace.repos['dotfiles'].source == 'https://github.com/user/dotfiles'

    def test_repo_default_manager(self, config_file: Path) -> None:
        result = load_config(config_file)
        assert result.workspace.repos['dotfiles'].manager == 'gh'

    def test_owner_bare_url_defaults_to_gh(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_bytes(b'[workspace.owners]\nmyorg = "https://github.com/myorg"\n')
        result = load_config(p)
        assert result.workspace.owners['myorg'].source == 'https://github.com/myorg'
        assert result.workspace.owners['myorg'].manager == 'gh'
        assert result.profiles == {}

    def test_owner_explicit_manager(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_text(
            '[workspace.owners]\n'
            'work = {source = "https://selfhosted.com/org", manager = "gitlab"}\n'
        )
        result = load_config(p)
        assert result.workspace.owners['work'].manager == 'gitlab'

    def test_missing_workspace_section_yields_empty_workspace(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_bytes(b'[profiles]\nwork = "https://github.com/org/dotfiles"\n')
        result = load_config(p)
        assert result.workspace.owners == {}
        assert result.workspace.repos == {}

    def test_parses_destination_from_workspace_section(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_bytes(b'[workspace]\ndestination = "/custom/workspace"\n')
        result = load_config(p)
        assert result.workspace.destination.target == Path('/custom/workspace')

    def test_destination_default_when_absent(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_bytes(b'[workspace.owners]\nmyorg = "https://github.com/myorg"\n')
        result = load_config(p)
        assert result.workspace.destination.target == Path.home() / 'workspace'


class TestLoadConfigTools:
    def test_parses_tool_entries(self, tmp_path: Path) -> None:
        manifest = tmp_path / 'mise.toml'
        manifest.touch()
        p = tmp_path / 'config.toml'
        p.write_text(f'[tools]\nwork-packages = {{manager = "mise", manifest = "{manifest}"}}\n')
        result = load_config(p)
        assert 'work-packages' in result.tools
        assert result.tools['work-packages'].manager == 'mise'

    def test_missing_tools_section_returns_empty(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_bytes(b'[profiles]\nwork = "url"\n')
        result = load_config(p)
        assert result.tools == {}


class TestLoadConfigEnv:
    def test_parses_env_entries(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_text('[env]\nwork = {engine = "mise", shell = "zsh"}\n')
        result = load_config(p)
        assert 'work' in result.env.entries
        assert result.env.entries['work'].engine == 'mise'
        assert result.env.entries['work'].shell == 'zsh'

    def test_parses_env_variables(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_text('[env.variables]\nATHOME_ENV = "production"\n')
        result = load_config(p)
        assert result.env.variables['ATHOME_ENV'] == 'production'

    def test_variables_not_treated_as_env_entry(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_text(
            '[env]\nwork = {engine = "mise", shell = "zsh"}\n\n[env.variables]\nFOO = "bar"\n'
        )
        result = load_config(p)
        assert 'variables' not in result.env.entries

    def test_missing_env_section_returns_empty(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_bytes(b'[profiles]\nwork = "url"\n')
        result = load_config(p)
        assert result.env.entries == {}
        assert result.env.variables == {}


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

    def test_profile_config_default_manager(self) -> None:
        p = ProfileConfig(name='x', source='url')
        assert p.manager == 'chezmoi'

    def test_profile_config_default_loads(self) -> None:
        p = ProfileConfig(name='x', source='url')
        assert p.loads == []

    def test_workspace_config_defaults(self) -> None:
        g = WorkspaceConfig()
        assert g.owners == {}
        assert g.repos == {}
        assert g.destination.target == Path.home() / 'workspace'

    def test_profile_backup_config_defaults(self) -> None:
        b = ProfileBackupConfig()
        assert b.default_backup == 'base'
        assert b.profile_backup == '{profile.name}'

    def test_env_config_defaults(self) -> None:
        e = EnvConfig()
        assert e.entries == {}
        assert e.variables == {}

    def test_athome_config_defaults(self) -> None:
        c = AthomeConfig()
        assert c.profiles == {}
        assert c.templates == {}
        assert isinstance(c.workspace, WorkspaceConfig)
        assert isinstance(c.profile_backup, ProfileBackupConfig)
        assert isinstance(c.env, EnvConfig)
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

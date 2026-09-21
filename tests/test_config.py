"""Tests for athome.definitions.config — configuration parser and path helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from athome.definitions.config import AthomeConfig
from athome.definitions.config import ProfileConfig
from athome.definitions.config import WorkspaceConfig
from athome.definitions.config import layer
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

    def test_parses_repo_entries(self, config_file: Path) -> None:
        result = load_config(config_file)
        assert result.workspace.repos['dotfiles'].source == 'https://github.com/user/dotfiles'

    def test_owner_bare_url(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_bytes(b'[workspace.owners]\nmyorg = "https://github.com/myorg"\n')
        result = load_config(p)
        assert result.workspace.owners['myorg'].source == 'https://github.com/myorg'
        assert result.profiles == {}

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


class TestLoadConfigBrew:
    def test_parses_brew_entries(self, tmp_path: Path) -> None:
        manifest = tmp_path / 'Brewfile'
        manifest.touch()
        p = tmp_path / 'config.toml'
        p.write_text(f'[brew]\nwork-packages = {{manifest = "{manifest}"}}\n')
        result = load_config(p)
        assert 'work-packages' in result.brew
        assert result.brew['work-packages'].manifest == manifest

    def test_bare_string_entry(self, tmp_path: Path) -> None:
        manifest = tmp_path / 'Brewfile'
        p = tmp_path / 'config.toml'
        p.write_text(f'[brew]\nwork-packages = "{manifest}"\n')
        result = load_config(p)
        assert result.brew['work-packages'].manifest == manifest

    def test_missing_brew_section_returns_empty(self, tmp_path: Path) -> None:
        p = tmp_path / 'config.toml'
        p.write_bytes(b'[profiles]\nwork = "url"\n')
        result = load_config(p)
        assert result.brew == {}


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

    def test_workspace_config_defaults(self) -> None:
        g = WorkspaceConfig()
        assert g.owners == {}
        assert g.repos == {}
        assert g.destination.target == Path.home() / 'workspace'

    def test_athome_config_defaults(self) -> None:
        c = AthomeConfig()
        assert c.profiles == {}
        assert c.templates == {}
        assert isinstance(c.workspace, WorkspaceConfig)


_P = ProfileConfig(name='myprofile', source='url')
_PX = ProfileConfig(name='x', source='url')
_PWORK = ProfileConfig(name='work', source='url')
_PPERSONAL = ProfileConfig(name='personal', source='url')


class TestLayer:
    def test_native_when_neither_marker_present(self, tmp_path: Path) -> None:
        with (
            patch('athome.definitions.config.CONTAINERENV_PATH', tmp_path / 'missing'),
            patch('athome.definitions.config.OSTREE_MARKER_PATH', tmp_path / 'missing'),
        ):
            assert layer() == 'native'

    def test_host_when_only_ostree_marker_present(self, tmp_path: Path) -> None:
        ostree = tmp_path / 'ostree-booted'
        ostree.touch()
        with (
            patch('athome.definitions.config.CONTAINERENV_PATH', tmp_path / 'missing'),
            patch('athome.definitions.config.OSTREE_MARKER_PATH', ostree),
        ):
            assert layer() == 'host'

    def test_dev_when_containerenv_present(self, tmp_path: Path) -> None:
        containerenv = tmp_path / 'containerenv'
        containerenv.touch()
        with (
            patch('athome.definitions.config.CONTAINERENV_PATH', containerenv),
            patch('athome.definitions.config.OSTREE_MARKER_PATH', tmp_path / 'ostree-booted'),
        ):
            assert layer() == 'dev'

    def test_dev_wins_when_both_markers_present(self, tmp_path: Path) -> None:
        """Distrobox can share /run with an atomic host, so both markers may be visible
        from inside the container — dev must win, matching .chezmoitemplates/layer."""
        containerenv = tmp_path / 'containerenv'
        containerenv.touch()
        ostree = tmp_path / 'ostree-booted'
        ostree.touch()
        with (
            patch('athome.definitions.config.CONTAINERENV_PATH', containerenv),
            patch('athome.definitions.config.OSTREE_MARKER_PATH', ostree),
        ):
            assert layer() == 'dev'


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
        """Layer-agnostic contract only: the exact name depends on the layer the
        suite happens to run on, and each layer is covered in isolation below."""
        p = profile_state_path('myprofile')
        assert p.suffix == '.db'
        assert p.name.startswith('myprofile')

    def test_profile_state_path_unsuffixed_on_native(self, tmp_path: Path) -> None:
        with (
            patch('athome.definitions.config.CONTAINERENV_PATH', tmp_path / 'missing'),
            patch('athome.definitions.config.OSTREE_MARKER_PATH', tmp_path / 'missing'),
        ):
            assert profile_state_path('myprofile').name == 'myprofile-state.db'

    def test_profile_state_path_suffixed_on_host(self, tmp_path: Path) -> None:
        ostree = tmp_path / 'ostree-booted'
        ostree.touch()
        with (
            patch('athome.definitions.config.CONTAINERENV_PATH', tmp_path / 'missing'),
            patch('athome.definitions.config.OSTREE_MARKER_PATH', ostree),
        ):
            assert profile_state_path('myprofile').name == 'myprofile-host-state.db'

    def test_profile_state_path_suffixed_on_dev(self, tmp_path: Path) -> None:
        containerenv = tmp_path / 'containerenv'
        containerenv.touch()
        with (
            patch('athome.definitions.config.CONTAINERENV_PATH', containerenv),
            patch('athome.definitions.config.OSTREE_MARKER_PATH', tmp_path / 'missing'),
        ):
            assert profile_state_path('myprofile').name == 'myprofile-dev-state.db'

    def test_host_and_dev_state_paths_never_collide(self, tmp_path: Path) -> None:
        ostree = tmp_path / 'ostree-booted'
        ostree.touch()
        with (
            patch('athome.definitions.config.CONTAINERENV_PATH', tmp_path / 'missing'),
            patch('athome.definitions.config.OSTREE_MARKER_PATH', ostree),
        ):
            host_path = profile_state_path('myprofile')

        containerenv = tmp_path / 'containerenv'
        containerenv.touch()
        with (
            patch('athome.definitions.config.CONTAINERENV_PATH', containerenv),
            patch('athome.definitions.config.OSTREE_MARKER_PATH', tmp_path / 'missing'),
        ):
            dev_path = profile_state_path('myprofile')

        assert host_path != dev_path

    def test_path_helpers_are_absolute(self) -> None:
        assert profile_source_path(_PX).is_absolute()
        assert profile_config_path('x').is_absolute()
        assert profile_state_path('x').is_absolute()

    def test_different_profiles_yield_different_paths(self) -> None:
        assert profile_source_path(_PWORK) != profile_source_path(_PPERSONAL)
        assert profile_config_path('work') != profile_config_path('personal')
        assert profile_state_path('work') != profile_state_path('personal')

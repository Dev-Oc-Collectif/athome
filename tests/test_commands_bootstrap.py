"""Tests for the bootstrap command — the config-circularity entry point."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

from typer.testing import CliRunner

from athome.cli.main import app
from athome.definitions.config import AthomeConfig
from athome.definitions.config import BrewEntryConfig
from athome.definitions.config import OwnerConfig
from athome.definitions.config import ProfileConfig
from athome.definitions.config import RepoConfig
from athome.definitions.config import TemplateConfig
from athome.definitions.config import WorkspaceConfig
from athome.exceptions import ConfigEntryExistsError

runner = CliRunner()

_SOURCE = 'https://github.com/cdubos-fr/chezcdubos-fr'
_PERSONAL = ProfileConfig(name='personal', source=_SOURCE)
_CFG_WITH_PERSONAL = AthomeConfig(profiles={'personal': _PERSONAL})
_EMPTY_CFG = AthomeConfig()


def _mock_manager(**kwargs: object) -> MagicMock:
    mgr = MagicMock()
    mgr.is_initialized.return_value = kwargs.get('initialized', True)
    return mgr


class TestRegisterPersonal:
    def test_registers_profile_writes_real_entry(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        src_dir = tmp_path / 'personal-src'
        src_dir.mkdir()
        with (
            patch('athome.cli.bootstrap.CONFIG_PATH', config_path),
            patch('athome.cli.bootstrap.load_config', return_value=_CFG_WITH_PERSONAL),
            patch('athome.cli.bootstrap._manager', _mock_manager(initialized=True)),
            patch('athome.cli.bootstrap.profile_source_path', return_value=src_dir),
        ):
            result = runner.invoke(app, ['bootstrap', _SOURCE])
        assert result.exit_code == 0, result.stderr
        assert f'personal = "{_SOURCE}"' in config_path.read_text()

    def test_prints_confirmation(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        src_dir = tmp_path / 'personal-src'
        src_dir.mkdir()
        with (
            patch('athome.cli.bootstrap.CONFIG_PATH', config_path),
            patch('athome.cli.bootstrap.load_config', return_value=_CFG_WITH_PERSONAL),
            patch('athome.cli.bootstrap._manager', _mock_manager(initialized=True)),
            patch('athome.cli.bootstrap.profile_source_path', return_value=src_dir),
        ):
            result = runner.invoke(app, ['bootstrap', _SOURCE])
        assert 'personal' in result.output
        assert _SOURCE in result.output

    def test_already_registered_prints_message_and_continues(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        src_dir = tmp_path / 'personal-src'
        src_dir.mkdir()
        with (
            patch('athome.cli.bootstrap.CONFIG_PATH', config_path),
            patch(
                'athome.cli.bootstrap.config_writer.add_profile',
                side_effect=ConfigEntryExistsError('personal', 'profiles'),
            ),
            patch('athome.cli.bootstrap.load_config', return_value=_CFG_WITH_PERSONAL),
            patch('athome.cli.bootstrap._manager', _mock_manager(initialized=True)),
            patch('athome.cli.bootstrap.profile_source_path', return_value=src_dir),
        ):
            result = runner.invoke(app, ['bootstrap', _SOURCE])
        assert result.exit_code == 0
        assert 'already registered' in result.output

    def test_source_mismatch_after_existing_registration_exits_one(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        with (
            patch('athome.cli.bootstrap.CONFIG_PATH', config_path),
            patch(
                'athome.cli.bootstrap.config_writer.add_profile',
                side_effect=ConfigEntryExistsError('personal', 'profiles'),
            ),
            patch('athome.cli.bootstrap.load_config', return_value=_EMPTY_CFG),
        ):
            result = runner.invoke(app, ['bootstrap', _SOURCE])
        assert result.exit_code == 1


class TestClonePersonal:
    def test_clones_when_not_initialized(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        src_dir = tmp_path / 'personal-src'
        src_dir.mkdir()
        mock_mgr = _mock_manager(initialized=False)
        with (
            patch('athome.cli.bootstrap.CONFIG_PATH', config_path),
            patch('athome.cli.bootstrap.load_config', return_value=_CFG_WITH_PERSONAL),
            patch('athome.cli.bootstrap._manager', mock_mgr),
            patch('athome.cli.bootstrap.profile_source_path', return_value=src_dir),
        ):
            result = runner.invoke(app, ['bootstrap', _SOURCE])
        assert result.exit_code == 0, result.stderr
        mock_mgr.init.assert_called_once_with(_PERSONAL)

    def test_skips_clone_when_already_initialized(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        src_dir = tmp_path / 'personal-src'
        src_dir.mkdir()
        mock_mgr = _mock_manager(initialized=True)
        with (
            patch('athome.cli.bootstrap.CONFIG_PATH', config_path),
            patch('athome.cli.bootstrap.load_config', return_value=_CFG_WITH_PERSONAL),
            patch('athome.cli.bootstrap._manager', mock_mgr),
            patch('athome.cli.bootstrap.profile_source_path', return_value=src_dir),
        ):
            result = runner.invoke(app, ['bootstrap', _SOURCE])
        assert result.exit_code == 0
        mock_mgr.init.assert_not_called()
        assert 'already initialized' in result.output


class TestMergeAthomeToml:
    def test_no_athome_toml_prints_guidance_and_stops(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        src_dir = tmp_path / 'personal-src'
        src_dir.mkdir()
        with (
            patch('athome.cli.bootstrap.CONFIG_PATH', config_path),
            patch('athome.cli.bootstrap.load_config', return_value=_CFG_WITH_PERSONAL),
            patch('athome.cli.bootstrap._manager', _mock_manager(initialized=True)),
            patch('athome.cli.bootstrap.profile_source_path', return_value=src_dir),
        ):
            result = runner.invoke(app, ['bootstrap', _SOURCE])
        assert result.exit_code == 0
        assert 'athome.toml' in result.output
        # Only the [profiles] section (from personal's own registration) exists.
        assert '[templates]' not in config_path.read_text()

    def test_merges_every_contributed_section(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        src_dir = tmp_path / 'personal-src'
        src_dir.mkdir()
        (src_dir / 'athome.toml').write_text('[workspace]\ndestination = "~/project"\n')
        contributed = AthomeConfig(
            profiles={'devoc': ProfileConfig(name='devoc', source='https://github.com/org/devoc')},
            templates={'python': TemplateConfig(source='https://github.com/org/python-template')},
            workspace=WorkspaceConfig(
                owners={'devoc-admin': OwnerConfig(source='https://github.com/devoc-admin')},
                repos={'secondbrain': RepoConfig(source='https://github.com/org/secondbrain')},
            ),
            brew={'personal': BrewEntryConfig(manifest=Path('/home/user/perso.Brewfile'))},
        )
        with (
            patch('athome.cli.bootstrap.CONFIG_PATH', config_path),
            patch(
                'athome.cli.bootstrap.load_config',
                side_effect=lambda path: (
                    contributed if path == src_dir / 'athome.toml' else _CFG_WITH_PERSONAL
                ),
            ),
            patch('athome.cli.bootstrap._manager', _mock_manager(initialized=True)),
            patch('athome.cli.bootstrap.profile_source_path', return_value=src_dir),
        ):
            result = runner.invoke(app, ['bootstrap', _SOURCE])
        assert result.exit_code == 0, result.stderr
        written = config_path.read_text()
        assert 'destination = "~/project"' in written
        assert 'devoc = "https://github.com/org/devoc"' in written
        assert 'python = "https://github.com/org/python-template"' in written
        assert 'devoc-admin = "https://github.com/devoc-admin"' in written
        assert 'secondbrain = "https://github.com/org/secondbrain"' in written
        assert 'personal = "/home/user/perso.Brewfile"' in written

    def test_no_destination_in_athome_toml_writes_none(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        src_dir = tmp_path / 'personal-src'
        src_dir.mkdir()
        (src_dir / 'athome.toml').write_text('[templates]\npython = "https://github.com/org/t"\n')
        contributed = AthomeConfig(
            templates={'python': TemplateConfig(source='https://github.com/org/t')},
        )
        with (
            patch('athome.cli.bootstrap.CONFIG_PATH', config_path),
            patch(
                'athome.cli.bootstrap.load_config',
                side_effect=lambda path: (
                    contributed if path == src_dir / 'athome.toml' else _CFG_WITH_PERSONAL
                ),
            ),
            patch('athome.cli.bootstrap._manager', _mock_manager(initialized=True)),
            patch('athome.cli.bootstrap.profile_source_path', return_value=src_dir),
        ):
            result = runner.invoke(app, ['bootstrap', _SOURCE])
        assert result.exit_code == 0, result.stderr
        assert '[workspace]' not in config_path.read_text()

    def test_merge_skips_entries_that_already_exist_locally(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        config_path.write_text(
            '[workspace]\ndestination = "~/local-only"\n\n[profiles]\ndevoc = "https://local/already-here"\n'
        )
        src_dir = tmp_path / 'personal-src'
        src_dir.mkdir()
        (src_dir / 'athome.toml').write_text('[workspace]\ndestination = "~/contributed"\n')
        contributed = AthomeConfig(
            profiles={'devoc': ProfileConfig(name='devoc', source='https://github.com/org/devoc')},
        )
        with (
            patch('athome.cli.bootstrap.CONFIG_PATH', config_path),
            patch(
                'athome.cli.bootstrap.load_config',
                side_effect=lambda path: (
                    contributed if path == src_dir / 'athome.toml' else _CFG_WITH_PERSONAL
                ),
            ),
            patch('athome.cli.bootstrap._manager', _mock_manager(initialized=True)),
            patch('athome.cli.bootstrap.profile_source_path', return_value=src_dir),
        ):
            result = runner.invoke(app, ['bootstrap', _SOURCE])
        assert result.exit_code == 0, result.stderr
        written = config_path.read_text()
        assert 'https://local/already-here' in written
        assert 'github.com/org/devoc' not in written
        assert '~/local-only' in written
        assert '~/contributed' not in written

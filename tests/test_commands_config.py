"""Tests for the config command group."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from athome.commands.config import app

runner = CliRunner()


class TestConfigInit:
    def test_creates_config_file(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        with patch('athome.commands.config.CONFIG_PATH', config_path):
            result = runner.invoke(app, ['init'])
        assert result.exit_code == 0
        assert config_path.exists()

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'deep' / 'nested' / 'config.toml'
        with patch('athome.commands.config.CONFIG_PATH', config_path):
            result = runner.invoke(app, ['init'])
        assert result.exit_code == 0
        assert config_path.exists()

    def test_prints_path_on_success(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        with patch('athome.commands.config.CONFIG_PATH', config_path):
            result = runner.invoke(app, ['init'])
        assert str(config_path) in result.output

    def test_does_not_overwrite_existing_without_force(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        config_path.write_text('existing')
        with patch('athome.commands.config.CONFIG_PATH', config_path):
            result = runner.invoke(app, ['init'])
        assert result.exit_code == 1
        assert config_path.read_text() == 'existing'

    def test_force_overwrites_existing(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        config_path.write_text('existing')
        with patch('athome.commands.config.CONFIG_PATH', config_path):
            result = runner.invoke(app, ['init', '--force'])
        assert result.exit_code == 0
        assert config_path.read_text() != 'existing'

    def test_template_contains_profiles_section(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        with patch('athome.commands.config.CONFIG_PATH', config_path):
            runner.invoke(app, ['init'])
        assert '[profiles]' in config_path.read_text()

    def test_template_contains_git_section(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        with patch('athome.commands.config.CONFIG_PATH', config_path):
            runner.invoke(app, ['init'])
        assert '[git]' in config_path.read_text()


class TestConfigShow:
    def test_missing_config_exits_one(self, tmp_path: Path) -> None:
        with patch('athome.commands.config.CONFIG_PATH', tmp_path / 'nonexistent.toml'):
            result = runner.invoke(app, ['show'])
        assert result.exit_code == 1

    def test_missing_config_prints_guidance(self, tmp_path: Path) -> None:
        with patch('athome.commands.config.CONFIG_PATH', tmp_path / 'nonexistent.toml'):
            result = runner.invoke(app, ['show'])
        assert 'setup' in result.stderr

    def test_existing_config_exits_zero(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        config_path.write_text('[profiles]\nwork = "url"\n')
        with patch('athome.commands.config.CONFIG_PATH', config_path):
            result = runner.invoke(app, ['show'])
        assert result.exit_code == 0

    def test_show_prints_file_content(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        config_path.write_text('[profiles]\nwork = "url"\n')
        with patch('athome.commands.config.CONFIG_PATH', config_path):
            result = runner.invoke(app, ['show'])
        assert 'work' in result.output


class TestConfigEdit:
    def test_missing_config_exits_one(self, tmp_path: Path) -> None:
        with patch('athome.commands.config.CONFIG_PATH', tmp_path / 'nonexistent.toml'):
            result = runner.invoke(app, ['edit'])
        assert result.exit_code == 1

    def test_launches_editor_from_visual(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        config_path.write_text('')
        with (
            patch('athome.commands.config.CONFIG_PATH', config_path),
            patch('athome.commands.config.subprocess.run') as mock_run,
            patch.dict('os.environ', {'VISUAL': 'code', 'EDITOR': 'nano'}),
        ):
            result = runner.invoke(app, ['edit'])
        assert result.exit_code == 0
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == 'code'

    def test_falls_back_to_editor_when_no_visual(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        config_path.write_text('')
        env = {'EDITOR': 'nano'}
        with (
            patch('athome.commands.config.CONFIG_PATH', config_path),
            patch('athome.commands.config.subprocess.run') as mock_run,
            patch.dict('os.environ', env, clear=True),
        ):
            result = runner.invoke(app, ['edit'])
        assert result.exit_code == 0
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == 'nano'

    def test_passes_config_path_to_editor(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        config_path.write_text('')
        with (
            patch('athome.commands.config.CONFIG_PATH', config_path),
            patch('athome.commands.config.subprocess.run') as mock_run,
            patch.dict('os.environ', {'EDITOR': 'vi'}),
        ):
            runner.invoke(app, ['edit'])
        cmd = mock_run.call_args[0][0]
        assert str(config_path) in cmd


@pytest.mark.parametrize('cmd', [['init'], ['show'], ['edit']])
def test_subcommands_reachable_via_help(cmd: list[str]) -> None:
    result = runner.invoke(app, ['--help'])
    assert result.exit_code == 0
    assert cmd[0] in result.output

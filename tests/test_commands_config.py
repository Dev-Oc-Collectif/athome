"""Tests for the config command group."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from athome.cli.config import app

runner = CliRunner()

# Input that says "no" to all interactive prompts (4 sections: profiles,
# templates, workspace, tools).
_ALL_NO = 'n\nn\nn\nn\n'

# Input that configures one profile then skips the rest.
_ONE_PROFILE = (
    'y\n'  # configure profiles?
    'personal\n'  # profile name
    'https://github.com/user/dots\n'  # source
    '\n'  # stop profile loop
    'n\nn\nn'  # skip templates, workspace, tools
)


class TestConfigInit:
    def test_creates_config_file(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        with patch('athome.cli.config.CONFIG_PATH', config_path):
            result = runner.invoke(app, ['init'], input=_ALL_NO)
        assert result.exit_code == 0
        assert config_path.exists()

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'deep' / 'nested' / 'config.toml'
        with patch('athome.cli.config.CONFIG_PATH', config_path):
            result = runner.invoke(app, ['init'], input=_ALL_NO)
        assert result.exit_code == 0
        assert config_path.exists()

    def test_prints_path_on_success(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        with patch('athome.cli.config.CONFIG_PATH', config_path):
            result = runner.invoke(app, ['init'], input=_ALL_NO)
        assert str(config_path) in result.output

    def test_does_not_overwrite_existing_without_force(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        config_path.write_text('existing')
        with patch('athome.cli.config.CONFIG_PATH', config_path):
            result = runner.invoke(app, ['init'])
        assert result.exit_code == 1
        assert config_path.read_text() == 'existing'

    def test_force_overwrites_existing(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        config_path.write_text('existing')
        with patch('athome.cli.config.CONFIG_PATH', config_path):
            result = runner.invoke(app, ['init', '--force'], input=_ALL_NO)
        assert result.exit_code == 0
        assert config_path.read_text() != 'existing'

    def test_profile_section_written_when_confirmed(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        with patch('athome.cli.config.CONFIG_PATH', config_path):
            runner.invoke(app, ['init'], input=_ONE_PROFILE)
        assert '[profiles]' in config_path.read_text()

    def test_profile_entry_written_with_name_and_source(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        with patch('athome.cli.config.CONFIG_PATH', config_path):
            runner.invoke(app, ['init'], input=_ONE_PROFILE)
        content = config_path.read_text()
        assert 'personal' in content
        assert 'https://github.com/user/dots' in content

    def test_workspace_section_uses_correct_key(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        workspace_input = (
            'n\nn\n'  # skip profiles, templates
            'y\n'  # configure workspace?
            '\n'  # destination (default ~/workspace)
            'y\n'  # add owners?
            'my-org\nhttps://github.com/my-org\n\n'  # one owner, stop
            'n\n'  # no repos
            'n\n'  # skip tools
        )
        with patch('athome.cli.config.CONFIG_PATH', config_path):
            runner.invoke(app, ['init'], input=workspace_input)
        content = config_path.read_text()
        assert '[workspace' in content
        assert '[git' not in content


class TestConfigShow:
    def test_missing_config_exits_one(self, tmp_path: Path) -> None:
        with patch('athome.cli.config.CONFIG_PATH', tmp_path / 'nonexistent.toml'):
            result = runner.invoke(app, ['show'])
        assert result.exit_code == 1

    def test_missing_config_prints_guidance(self, tmp_path: Path) -> None:
        with patch('athome.cli.config.CONFIG_PATH', tmp_path / 'nonexistent.toml'):
            result = runner.invoke(app, ['show'])
        assert 'setup' in result.stderr

    def test_existing_config_exits_zero(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        config_path.write_text('[profiles]\nwork = "url"\n')
        with patch('athome.cli.config.CONFIG_PATH', config_path):
            result = runner.invoke(app, ['show'])
        assert result.exit_code == 0

    def test_show_prints_file_content(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        config_path.write_text('[profiles]\nwork = "url"\n')
        with patch('athome.cli.config.CONFIG_PATH', config_path):
            result = runner.invoke(app, ['show'])
        assert 'work' in result.output


class TestConfigEdit:
    def test_missing_config_exits_one(self, tmp_path: Path) -> None:
        with patch('athome.cli.config.CONFIG_PATH', tmp_path / 'nonexistent.toml'):
            result = runner.invoke(app, ['edit'])
        assert result.exit_code == 1

    def test_launches_editor_from_visual(self, tmp_path: Path) -> None:
        config_path = tmp_path / 'config.toml'
        config_path.write_text('')
        with (
            patch('athome.cli.config.CONFIG_PATH', config_path),
            patch('athome.cli.config.subprocess.run') as mock_run,
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
            patch('athome.cli.config.CONFIG_PATH', config_path),
            patch('athome.cli.config.subprocess.run') as mock_run,
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
            patch('athome.cli.config.CONFIG_PATH', config_path),
            patch('athome.cli.config.subprocess.run') as mock_run,
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

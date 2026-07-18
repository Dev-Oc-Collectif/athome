"""Tests for the project command group."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from athome.cli.project import app
from athome.definitions.config import AthomeConfig
from athome.definitions.config import TemplateConfig

runner = CliRunner()

_CFG = AthomeConfig(
    templates={
        'python': TemplateConfig(source='https://github.com/Dev-Oc-Collectif/python-template'),
    },
)
_EMPTY_CFG = AthomeConfig()


class TestProjectCreate:
    def test_named_template_resolves_url_from_config(self, tmp_path: Path) -> None:
        with (
            patch('athome.commands.project.load_config', return_value=_CFG),
            patch('athome.commands.project._engine.create') as mock_create,
        ):
            runner.invoke(app, ['create', 'python', str(tmp_path / 'proj')])
        mock_create.assert_called_once_with(
            'https://github.com/Dev-Oc-Collectif/python-template',
            tmp_path / 'proj',
        )

    def test_direct_url_passthrough(self, tmp_path: Path) -> None:
        direct_url = 'https://github.com/other/template'
        with (
            patch('athome.commands.project.load_config', return_value=_EMPTY_CFG),
            patch('athome.commands.project._engine.create') as mock_create,
        ):
            runner.invoke(app, ['create', direct_url, str(tmp_path / 'proj')])
        mock_create.assert_called_once_with(direct_url, tmp_path / 'proj')

    def test_prints_creating_message(self, tmp_path: Path) -> None:
        with (
            patch('athome.commands.project.load_config', return_value=_CFG),
            patch('athome.commands.project._engine.create'),
        ):
            result = runner.invoke(app, ['create', 'python', str(tmp_path / 'proj')])
        assert 'Creating project' in result.output

    def test_exit_code_zero_on_success(self, tmp_path: Path) -> None:
        with (
            patch('athome.commands.project.load_config', return_value=_CFG),
            patch('athome.commands.project._engine.create'),
        ):
            result = runner.invoke(app, ['create', 'python', str(tmp_path / 'proj')])
        assert result.exit_code == 0


class TestProjectUpdate:
    def test_default_destination_is_current_dir(self) -> None:
        with patch('athome.commands.project._engine.update') as mock_update:
            result = runner.invoke(app, ['update'])
        assert result.exit_code == 0
        mock_update.assert_called_once_with(Path('.'))

    def test_explicit_destination_passed(self, tmp_path: Path) -> None:
        with patch('athome.commands.project._engine.update') as mock_update:
            result = runner.invoke(app, ['update', str(tmp_path)])
        assert result.exit_code == 0
        mock_update.assert_called_once_with(tmp_path)

    def test_prints_updating_message(self, tmp_path: Path) -> None:
        with patch('athome.commands.project._engine.update'):
            result = runner.invoke(app, ['update', str(tmp_path)])
        assert 'Updating project' in result.output

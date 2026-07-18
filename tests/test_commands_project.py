"""Tests for the project command group."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from athome.cli import project as project_module
from athome.cli.project import app
from athome.definitions.config import AthomeConfig
from athome.definitions.config import TemplateConfig

runner = CliRunner()

_CFG = AthomeConfig(
    templates={
        'python': TemplateConfig(source='https://github.com/Dev-Oc-Collectif/python-template'),
        'rust': TemplateConfig(source='https://github.com/org/rust-template', manager='cruft'),
    },
)
_EMPTY_CFG = AthomeConfig()


class TestProjectCreate:
    def test_named_template_resolves_url_from_config(self, tmp_path: Path) -> None:
        with (
            patch('athome.cli.project.load_config', return_value=_CFG),
            patch.object(project_module._ENGINES['copier'], 'create') as mock_create,
        ):
            runner.invoke(app, ['create', 'python', str(tmp_path / 'proj')])
        mock_create.assert_called_once_with(
            'https://github.com/Dev-Oc-Collectif/python-template',
            tmp_path / 'proj',
        )

    def test_direct_url_passthrough(self, tmp_path: Path) -> None:
        direct_url = 'https://github.com/other/template'
        with (
            patch('athome.cli.project.load_config', return_value=_EMPTY_CFG),
            patch.object(project_module._ENGINES['copier'], 'create') as mock_create,
        ):
            runner.invoke(app, ['create', direct_url, str(tmp_path / 'proj')])
        mock_create.assert_called_once_with(direct_url, tmp_path / 'proj')

    def test_cruft_manager_selected_from_config(self, tmp_path: Path) -> None:
        with (
            patch('athome.cli.project.load_config', return_value=_CFG),
            patch.object(project_module._ENGINES['cruft'], 'create') as mock_create,
            patch.object(project_module._ENGINES['copier'], 'create') as mock_copier_create,
        ):
            runner.invoke(app, ['create', 'rust', str(tmp_path / 'proj')])
        mock_create.assert_called_once_with(
            'https://github.com/org/rust-template',
            tmp_path / 'proj',
        )
        mock_copier_create.assert_not_called()

    def test_prints_creating_message(self, tmp_path: Path) -> None:
        with (
            patch('athome.cli.project.load_config', return_value=_CFG),
            patch.object(project_module._ENGINES['copier'], 'create'),
        ):
            result = runner.invoke(app, ['create', 'python', str(tmp_path / 'proj')])
        assert 'Creating project' in result.output

    def test_exit_code_zero_on_success(self, tmp_path: Path) -> None:
        with (
            patch('athome.cli.project.load_config', return_value=_CFG),
            patch.object(project_module._ENGINES['copier'], 'create'),
        ):
            result = runner.invoke(app, ['create', 'python', str(tmp_path / 'proj')])
        assert result.exit_code == 0


class TestProjectUpdate:
    def test_default_destination_is_current_dir(self) -> None:
        with patch.object(project_module._ENGINES['copier'], 'update') as mock_update:
            result = runner.invoke(app, ['update'])
        assert result.exit_code == 0
        mock_update.assert_called_once_with(Path('.'))

    def test_explicit_destination_passed(self, tmp_path: Path) -> None:
        with patch.object(project_module._ENGINES['copier'], 'update') as mock_update:
            result = runner.invoke(app, ['update', str(tmp_path)])
        assert result.exit_code == 0
        mock_update.assert_called_once_with(tmp_path)

    def test_prints_updating_message(self, tmp_path: Path) -> None:
        with patch.object(project_module._ENGINES['copier'], 'update'):
            result = runner.invoke(app, ['update', str(tmp_path)])
        assert 'Updating project' in result.output

    def test_manager_flag_selects_engine(self, tmp_path: Path) -> None:
        with (
            patch.object(project_module._ENGINES['cruft'], 'update') as mock_update,
            patch.object(project_module._ENGINES['copier'], 'update') as mock_copier_update,
        ):
            result = runner.invoke(app, ['update', str(tmp_path), '--manager', 'cruft'])
        assert result.exit_code == 0
        mock_update.assert_called_once_with(tmp_path)
        mock_copier_update.assert_not_called()

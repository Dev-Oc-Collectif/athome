"""Tests for the template command group."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from athome.cli import templates as templates_module
from athome.cli.templates import app
from athome.definitions.config import AthomeConfig
from athome.definitions.config import TemplateConfig

runner = CliRunner()

_CFG = AthomeConfig(
    templates={
        'python': TemplateConfig(source='https://github.com/Dev-Oc-Collectif/python-template'),
        'zola': TemplateConfig(source='https://github.com/Dev-Oc-Collectif/zola-template'),
        'rust': TemplateConfig(source='https://github.com/org/rust-template', manager='cruft'),
    }
)
_EMPTY_CFG = AthomeConfig()


class TestTemplateList:
    def test_empty_config_prints_guidance(self) -> None:
        with patch('athome.cli.templates.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['list'])
        assert result.exit_code == 0
        assert '[templates]' in result.output

    def test_shows_template_names(self) -> None:
        with patch('athome.cli.templates.load_config', return_value=_CFG):
            result = runner.invoke(app, ['list'])
        assert 'python' in result.output
        assert 'zola' in result.output

    def test_shows_template_urls(self) -> None:
        with patch('athome.cli.templates.load_config', return_value=_CFG):
            result = runner.invoke(app, ['list'])
        assert 'https://github.com/Dev-Oc-Collectif/python-template' in result.output

    def test_exit_code_zero(self) -> None:
        with patch('athome.cli.templates.load_config', return_value=_CFG):
            result = runner.invoke(app, ['list'])
        assert result.exit_code == 0


class TestTemplateAdd:
    def test_calls_config_writer_with_parsed_args(self) -> None:
        with patch('athome.cli.templates.config_writer.add_template') as mock_add:
            result = runner.invoke(
                app, ['add', 'rust', 'https://github.com/org/rust-template', '--manager', 'cruft']
            )
        assert result.exit_code == 0
        mock_add.assert_called_once()
        args, kwargs = mock_add.call_args
        assert args[0] == 'rust'
        assert args[1] == 'https://github.com/org/rust-template'
        assert kwargs['manager'] == 'cruft'

    def test_default_manager_passed_as_copier(self) -> None:
        with patch('athome.cli.templates.config_writer.add_template') as mock_add:
            runner.invoke(app, ['add', 'rust', 'https://github.com/org/rust-template'])
        assert mock_add.call_args.kwargs['manager'] == 'copier'

    def test_unknown_manager_exits_one(self) -> None:
        with patch('athome.cli.templates.config_writer.add_template') as mock_add:
            result = runner.invoke(
                app, ['add', 'rust', 'https://github.com/org/rust-template', '--manager', 'nope']
            )
        assert result.exit_code == 1
        mock_add.assert_not_called()

    def test_prints_confirmation(self) -> None:
        with patch('athome.cli.templates.config_writer.add_template'):
            result = runner.invoke(app, ['add', 'rust', 'https://github.com/org/rust-template'])
        assert 'rust' in result.output


class TestTemplateUse:
    # -- create action ---------------------------------------------------

    def test_create_named_template_resolves_url_from_config(self, tmp_path: Path) -> None:
        with (
            patch('athome.cli.templates.load_config', return_value=_CFG),
            patch.object(templates_module._ENGINES['copier'], 'create') as mock_create,
        ):
            runner.invoke(app, ['use', 'python', 'create', str(tmp_path / 'proj')])
        mock_create.assert_called_once_with(
            'https://github.com/Dev-Oc-Collectif/python-template',
            tmp_path / 'proj',
            data=None,
            trust=False,
        )

    def test_create_direct_url_passthrough(self, tmp_path: Path) -> None:
        direct_url = 'https://github.com/other/template'
        with (
            patch('athome.cli.templates.load_config', return_value=_EMPTY_CFG),
            patch.object(templates_module._ENGINES['copier'], 'create') as mock_create,
        ):
            runner.invoke(app, ['use', direct_url, 'create', str(tmp_path / 'proj')])
        mock_create.assert_called_once_with(direct_url, tmp_path / 'proj', data=None, trust=False)

    def test_create_cruft_manager_selected_from_config(self, tmp_path: Path) -> None:
        with (
            patch('athome.cli.templates.load_config', return_value=_CFG),
            patch.object(templates_module._ENGINES['cruft'], 'create') as mock_create,
            patch.object(templates_module._ENGINES['copier'], 'create') as mock_copier_create,
        ):
            runner.invoke(app, ['use', 'rust', 'create', str(tmp_path / 'proj')])
        mock_create.assert_called_once_with(
            'https://github.com/org/rust-template', tmp_path / 'proj', data=None, trust=False
        )
        mock_copier_create.assert_not_called()

    def test_create_prints_creating_message(self, tmp_path: Path) -> None:
        with (
            patch('athome.cli.templates.load_config', return_value=_CFG),
            patch.object(templates_module._ENGINES['copier'], 'create'),
        ):
            result = runner.invoke(app, ['use', 'python', 'create', str(tmp_path / 'proj')])
        assert 'Creating project' in result.output

    def test_create_exit_code_zero_on_success(self, tmp_path: Path) -> None:
        with (
            patch('athome.cli.templates.load_config', return_value=_CFG),
            patch.object(templates_module._ENGINES['copier'], 'create'),
        ):
            result = runner.invoke(app, ['use', 'python', 'create', str(tmp_path / 'proj')])
        assert result.exit_code == 0

    # -- update action (now resolves manager from config — the friction fix) --

    def test_update_default_destination_is_current_dir(self) -> None:
        with (
            patch('athome.cli.templates.load_config', return_value=_CFG),
            patch.object(templates_module._ENGINES['copier'], 'update') as mock_update,
        ):
            result = runner.invoke(app, ['use', 'python', 'update'])
        assert result.exit_code == 0
        mock_update.assert_called_once_with(Path('.'), data=None, trust=False)

    def test_update_explicit_destination_passed(self, tmp_path: Path) -> None:
        with (
            patch('athome.cli.templates.load_config', return_value=_CFG),
            patch.object(templates_module._ENGINES['copier'], 'update') as mock_update,
        ):
            result = runner.invoke(app, ['use', 'python', 'update', str(tmp_path)])
        assert result.exit_code == 0
        mock_update.assert_called_once_with(tmp_path, data=None, trust=False)

    def test_update_prints_updating_message(self, tmp_path: Path) -> None:
        with (
            patch('athome.cli.templates.load_config', return_value=_CFG),
            patch.object(templates_module._ENGINES['copier'], 'update'),
        ):
            result = runner.invoke(app, ['use', 'python', 'update', str(tmp_path)])
        assert 'Updating project' in result.output

    def test_update_manager_resolved_from_config_without_a_manager_flag(
        self, tmp_path: Path
    ) -> None:
        """The exact friction fix: update no longer needs a --manager flag."""
        with (
            patch('athome.cli.templates.load_config', return_value=_CFG),
            patch.object(templates_module._ENGINES['cruft'], 'update') as mock_update,
            patch.object(templates_module._ENGINES['copier'], 'update') as mock_copier_update,
        ):
            result = runner.invoke(app, ['use', 'rust', 'update', str(tmp_path)])
        assert result.exit_code == 0
        mock_update.assert_called_once_with(tmp_path, data=None, trust=False)
        mock_copier_update.assert_not_called()

    # -- sync action -------------------------------------------------------

    def test_sync_creates_when_not_initialized(self, tmp_path: Path) -> None:
        with (
            patch('athome.cli.templates.load_config', return_value=_CFG),
            patch.object(templates_module._ENGINES['copier'], 'is_initialized', return_value=False),
            patch.object(templates_module._ENGINES['copier'], 'create') as mock_create,
            patch.object(templates_module._ENGINES['copier'], 'update') as mock_update,
        ):
            result = runner.invoke(app, ['use', 'python', 'sync', str(tmp_path)])
        assert result.exit_code == 0
        mock_create.assert_called_once()
        mock_update.assert_not_called()

    def test_sync_updates_when_already_initialized(self, tmp_path: Path) -> None:
        with (
            patch('athome.cli.templates.load_config', return_value=_CFG),
            patch.object(templates_module._ENGINES['copier'], 'is_initialized', return_value=True),
            patch.object(templates_module._ENGINES['copier'], 'create') as mock_create,
            patch.object(templates_module._ENGINES['copier'], 'update') as mock_update,
        ):
            result = runner.invoke(app, ['use', 'python', 'sync', str(tmp_path)])
        assert result.exit_code == 0
        mock_update.assert_called_once()
        mock_create.assert_not_called()

    # -- action validation ---------------------------------------------------

    def test_unknown_action_exits_one(self, tmp_path: Path) -> None:
        with patch('athome.cli.templates.load_config', return_value=_CFG):
            result = runner.invoke(app, ['use', 'python', 'bogus', str(tmp_path)])
        assert result.exit_code == 1

    # -- --trust / --data passthrough ----------------------------------------

    def test_trust_flag_forwarded(self, tmp_path: Path) -> None:
        with (
            patch('athome.cli.templates.load_config', return_value=_CFG),
            patch.object(templates_module._ENGINES['copier'], 'create') as mock_create,
        ):
            runner.invoke(app, ['use', 'python', 'create', str(tmp_path), '--trust'])
        assert mock_create.call_args.kwargs['trust'] is True

    def test_data_flags_parsed_and_forwarded(self, tmp_path: Path) -> None:
        with (
            patch('athome.cli.templates.load_config', return_value=_CFG),
            patch.object(templates_module._ENGINES['copier'], 'create') as mock_create,
        ):
            runner.invoke(
                app,
                [
                    'use',
                    'python',
                    'create',
                    str(tmp_path),
                    '--data',
                    'name=demo',
                    '--data',
                    'license=MIT',
                ],
            )
        assert mock_create.call_args.kwargs['data'] == {'name': 'demo', 'license': 'MIT'}

    def test_malformed_data_entry_exits_one(self, tmp_path: Path) -> None:
        with (
            patch('athome.cli.templates.load_config', return_value=_CFG),
            patch.object(templates_module._ENGINES['copier'], 'create') as mock_create,
        ):
            result = runner.invoke(
                app, ['use', 'python', 'create', str(tmp_path), '--data', 'no-equals-sign']
            )
        assert result.exit_code == 1
        mock_create.assert_not_called()

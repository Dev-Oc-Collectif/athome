"""Tests for the template command group."""

from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from athome.cli.templates import app
from athome.definitions.config import AthomeConfig
from athome.definitions.config import TemplateConfig

runner = CliRunner()

_CFG = AthomeConfig(
    templates={
        'python': TemplateConfig(source='https://github.com/Dev-Oc-Collectif/python-template'),
        'zola': TemplateConfig(source='https://github.com/Dev-Oc-Collectif/zola-template'),
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

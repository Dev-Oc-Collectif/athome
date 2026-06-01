"""Tests for the template command group."""

from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from athome.commands.template import app
from athome.config import AthomeConfig

runner = CliRunner()

_CFG = AthomeConfig(
    templates={
        'python': 'https://github.com/Dev-Oc-Collectif/python-template',
        'zola': 'https://github.com/Dev-Oc-Collectif/zola-template',
    }
)
_EMPTY_CFG = AthomeConfig()


class TestTemplateList:
    def test_empty_config_prints_guidance(self) -> None:
        with patch('athome.commands.template.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, [])
        assert result.exit_code == 0
        assert '[templates]' in result.output

    def test_shows_template_names(self) -> None:
        with patch('athome.commands.template.load_config', return_value=_CFG):
            result = runner.invoke(app, [])
        assert 'python' in result.output
        assert 'zola' in result.output

    def test_shows_template_urls(self) -> None:
        with patch('athome.commands.template.load_config', return_value=_CFG):
            result = runner.invoke(app, [])
        assert 'https://github.com/Dev-Oc-Collectif/python-template' in result.output

    def test_exit_code_zero(self) -> None:
        with patch('athome.commands.template.load_config', return_value=_CFG):
            result = runner.invoke(app, [])
        assert result.exit_code == 0

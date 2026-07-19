"""Tests for the main app — wiring, aliases, and top-level help."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from athome.cli import templates as templates_module
from athome.cli.main import app
from athome.definitions.config import AthomeConfig
from athome.definitions.config import TemplateConfig

runner = CliRunner()

_CFG = AthomeConfig(
    templates={
        'python': TemplateConfig(source='https://github.com/Dev-Oc-Collectif/python-template'),
    }
)
_EMPTY_CFG = AthomeConfig()


class TestHelp:
    def test_root_help_exits_zero(self) -> None:
        result = runner.invoke(app, ['--help'])
        assert result.exit_code == 0

    def test_root_help_lists_profile(self) -> None:
        result = runner.invoke(app, ['--help'])
        assert 'profile' in result.output

    def test_root_help_lists_repo(self) -> None:
        result = runner.invoke(app, ['--help'])
        assert 'repo' in result.output

    def test_root_help_lists_create_alias(self) -> None:
        result = runner.invoke(app, ['--help'])
        assert 'create' in result.output

    def test_root_help_lists_templates_alias(self) -> None:
        result = runner.invoke(app, ['--help'])
        assert 'templates' in result.output

    def test_root_help_lists_setup_alias(self) -> None:
        result = runner.invoke(app, ['--help'])
        assert 'setup' in result.output

    def test_root_help_lists_config(self) -> None:
        result = runner.invoke(app, ['--help'])
        assert 'config' in result.output

    def test_no_args_shows_help(self) -> None:
        result = runner.invoke(app, [])
        # no_args_is_help=True shows help and exits 2 in Typer 0.25
        assert 'athome' in result.output or result.exit_code in (0, 2)


class TestCreateAlias:
    def test_create_alias_resolves_template_from_config(self, tmp_path: Path) -> None:
        with (
            patch('athome.cli.templates.load_config', return_value=_CFG),
            patch.object(templates_module._ENGINES['copier'], 'create') as mock_create,
        ):
            result = runner.invoke(app, ['create', 'python', str(tmp_path / 'p')])
        assert result.exit_code == 0
        mock_create.assert_called_once_with(
            'https://github.com/Dev-Oc-Collectif/python-template',
            tmp_path / 'p',
            data=None,
            trust=False,
        )

    def test_create_alias_with_direct_url(self, tmp_path: Path) -> None:
        url = 'https://github.com/other/template'
        with (
            patch('athome.cli.templates.load_config', return_value=_EMPTY_CFG),
            patch.object(templates_module._ENGINES['copier'], 'create') as mock_create,
        ):
            runner.invoke(app, ['create', url, str(tmp_path / 'p')])
        mock_create.assert_called_once_with(url, tmp_path / 'p', data=None, trust=False)


class TestTemplatesAlias:
    def test_templates_alias_shows_names(self) -> None:
        with patch('athome.cli.templates.load_config', return_value=_CFG):
            result = runner.invoke(app, ['templates'])
        assert 'python' in result.output

    def test_templates_alias_empty_config_prints_guidance(self) -> None:
        with patch('athome.cli.templates.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['templates'])
        assert result.exit_code == 0
        assert '[templates]' in result.output


class TestSubCommandRouting:
    def test_profile_subgroup_reachable(self) -> None:
        result = runner.invoke(app, ['profile', '--help'])
        assert result.exit_code == 0
        assert 'sync' in result.output

    def test_system_subgroup_reachable(self) -> None:
        result = runner.invoke(app, ['system', '--help'])
        assert result.exit_code == 0

    def test_repo_subgroup_reachable(self) -> None:
        result = runner.invoke(app, ['repo', '--help'])
        assert result.exit_code == 0

    def test_template_subgroup_reachable(self) -> None:
        result = runner.invoke(app, ['template', '--help'])
        assert result.exit_code == 0

    def test_config_subgroup_reachable(self) -> None:
        result = runner.invoke(app, ['config', '--help'])
        assert result.exit_code == 0

    def test_mise_subgroup_reachable(self) -> None:
        result = runner.invoke(app, ['mise', '--help'])
        assert result.exit_code == 0

    def test_brew_subgroup_reachable(self) -> None:
        result = runner.invoke(app, ['brew', '--help'])
        assert result.exit_code == 0

    def test_cleanup_command_reachable(self) -> None:
        result = runner.invoke(app, ['cleanup', '--help'])
        assert result.exit_code == 0

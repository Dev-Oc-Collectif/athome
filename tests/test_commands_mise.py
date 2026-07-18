"""Tests for the mise command group (cross-profile config alignment)."""

from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from athome.cli.mise import app
from athome.definitions.config import AthomeConfig
from athome.definitions.config import ProfileConfig
from athome.tools.mise_align import ToolDrift

runner = CliRunner()

_CFG = AthomeConfig(
    profiles={'work': ProfileConfig(name='work', source='https://github.com/org/dotfiles-work')},
)
_EMPTY_CFG = AthomeConfig()


class TestMiseCheck:
    def test_no_profiles_prints_guidance(self) -> None:
        with patch('athome.cli.mise.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, [])
        assert result.exit_code == 0
        assert '[profiles]' in result.output

    def test_no_drift_exits_zero(self) -> None:
        with (
            patch('athome.cli.mise.load_config', return_value=_CFG),
            patch('athome.cli.mise.find_drift', return_value=[]),
        ):
            result = runner.invoke(app, [])
        assert result.exit_code == 0
        assert 'aligned' in result.output

    def test_drift_exits_one(self) -> None:
        drift = ToolDrift(tool='node', versions={'work': '20', 'personal': '22'})
        with (
            patch('athome.cli.mise.load_config', return_value=_CFG),
            patch('athome.cli.mise.find_drift', return_value=[drift]),
        ):
            result = runner.invoke(app, [])
        assert result.exit_code == 1

    def test_drift_output_lists_tool_and_versions(self) -> None:
        drift = ToolDrift(tool='node', versions={'work': '20', 'personal': '22'})
        with (
            patch('athome.cli.mise.load_config', return_value=_CFG),
            patch('athome.cli.mise.find_drift', return_value=[drift]),
        ):
            result = runner.invoke(app, [])
        assert 'node' in result.output
        assert 'work' in result.output
        assert '20' in result.output
        assert 'personal' in result.output
        assert '22' in result.output

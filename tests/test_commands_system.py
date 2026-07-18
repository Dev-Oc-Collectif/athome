"""Tests for the system command group."""

from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from athome.cli.system import _REQUIRED_TOOLS
from athome.cli.system import app

runner = CliRunner()


def _all_present(tool: str) -> str | None:
    return f'/usr/bin/{tool}'


def _none_present(_tool: str) -> None:
    return None


class TestSystemDoctor:
    def test_all_tools_present_exits_zero(self) -> None:
        with patch('athome.cli.system.shutil.which', side_effect=_all_present):
            result = runner.invoke(app, [])
        assert result.exit_code == 0

    def test_all_tools_present_prints_check_marks(self) -> None:
        with patch('athome.cli.system.shutil.which', side_effect=_all_present):
            result = runner.invoke(app, [])
        assert '✓' in result.output

    def test_missing_tool_exits_one(self) -> None:
        with patch('athome.cli.system.shutil.which', side_effect=_none_present):
            result = runner.invoke(app, [])
        assert result.exit_code == 1

    def test_missing_tool_prints_cross_mark(self) -> None:
        with patch('athome.cli.system.shutil.which', side_effect=_none_present):
            result = runner.invoke(app, [])
        assert '✗' in result.output

    def test_partial_tools_shows_both_marks(self) -> None:
        present = {'chezmoi', 'gh'}

        def side_effect(tool: str) -> str | None:
            return f'/usr/bin/{tool}' if tool in present else None

        with patch('athome.cli.system.shutil.which', side_effect=side_effect):
            result = runner.invoke(app, [])
        assert '✓' in result.output
        assert '✗' in result.output

    def test_all_required_tools_checked(self) -> None:
        checked: list[str] = []
        with patch(
            'athome.cli.system.shutil.which',
            side_effect=checked.append,
        ):
            runner.invoke(app, [])
        for tool in _REQUIRED_TOOLS:
            assert tool in checked

"""Tests for the system command group."""

from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from athome.commands.system import _REQUIRED_TOOLS
from athome.commands.system import app

runner = CliRunner()


def _all_present(tool: str) -> str | None:
    return f'/usr/bin/{tool}'


def _none_present(_tool: str) -> None:
    return None


class TestSystemDoctor:
    def test_all_tools_present_exits_zero(self) -> None:
        with patch('athome.commands.system.shutil.which', side_effect=_all_present):
            result = runner.invoke(app, ['doctor'])
        assert result.exit_code == 0

    def test_all_tools_present_prints_check_marks(self) -> None:
        with patch('athome.commands.system.shutil.which', side_effect=_all_present):
            result = runner.invoke(app, ['doctor'])
        assert '✓' in result.output

    def test_missing_tool_exits_one(self) -> None:
        with patch('athome.commands.system.shutil.which', side_effect=_none_present):
            result = runner.invoke(app, ['doctor'])
        assert result.exit_code == 1

    def test_missing_tool_prints_cross_mark(self) -> None:
        with patch('athome.commands.system.shutil.which', side_effect=_none_present):
            result = runner.invoke(app, ['doctor'])
        assert '✗' in result.output

    def test_partial_tools_shows_both_marks(self) -> None:
        present = {'uv', 'just'}

        def side_effect(tool: str) -> str | None:
            return f'/usr/bin/{tool}' if tool in present else None

        with patch('athome.commands.system.shutil.which', side_effect=side_effect):
            result = runner.invoke(app, ['doctor'])
        assert '✓' in result.output
        assert '✗' in result.output

    def test_all_required_tools_checked(self) -> None:
        checked: list[str] = []
        with patch(
            'athome.commands.system.shutil.which',
            side_effect=checked.append,
        ):
            runner.invoke(app, ['doctor'])
        for tool in _REQUIRED_TOOLS:
            assert tool in checked


class TestSystemUpgrade:
    def test_mise_missing_exits_one(self) -> None:
        with patch('athome.commands.system.shutil.which', return_value=None):
            result = runner.invoke(app, ['upgrade'])
        assert result.exit_code == 1

    def test_mise_missing_prints_error(self) -> None:
        with patch('athome.commands.system.shutil.which', return_value=None):
            result = runner.invoke(app, ['upgrade'])
        assert 'mise' in result.stderr

    def test_mise_present_calls_upgrade(self) -> None:
        with (
            patch('athome.commands.system.shutil.which', return_value='/usr/bin/mise'),
            patch('athome.commands.system._mise.upgrade') as mock_upgrade,
        ):
            result = runner.invoke(app, ['upgrade'])
        assert result.exit_code == 0
        mock_upgrade.assert_called_once_with()

    def test_mise_present_prints_message(self) -> None:
        with (
            patch('athome.commands.system.shutil.which', return_value='/usr/bin/mise'),
            patch('athome.commands.system._mise.upgrade'),
        ):
            result = runner.invoke(app, ['upgrade'])
        assert 'mise' in result.output.lower()

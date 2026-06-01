"""Tests for CopierEngine — TemplateEngine backed by copier."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from athome.interfaces.template_engine import TemplateEngine
from athome.templates_managers.copier import CopierEngine


class TestCopierEngineContract:
    def test_is_template_engine(self) -> None:
        assert issubclass(CopierEngine, TemplateEngine)

    def test_instantiates(self) -> None:
        assert isinstance(CopierEngine(), CopierEngine)


class TestCreate:
    def test_calls_run_copy(self) -> None:
        engine = CopierEngine()
        with patch('athome.templates_managers.copier.copier.run_copy') as mock_copy:
            engine.create('https://example.com/template', Path('/dest'))
        mock_copy.assert_called_once()

    def test_passes_url_as_first_arg(self) -> None:
        engine = CopierEngine()
        url = 'https://github.com/org/template'
        with patch('athome.templates_managers.copier.copier.run_copy') as mock_copy:
            engine.create(url, Path('/dest'))
        assert mock_copy.call_args[0][0] == url

    def test_passes_destination_as_string(self) -> None:
        engine = CopierEngine()
        dest = Path('/my/project')
        with patch('athome.templates_managers.copier.copier.run_copy') as mock_copy:
            engine.create('https://example.com/t', dest)
        assert mock_copy.call_args[0][1] == str(dest)


class TestUpdate:
    def test_calls_run_update(self) -> None:
        engine = CopierEngine()
        with patch('athome.templates_managers.copier.copier.run_update') as mock_update:
            engine.update(Path('/my/project'))
        mock_update.assert_called_once()

    def test_passes_destination_as_string(self) -> None:
        engine = CopierEngine()
        dest = Path('/my/project')
        with patch('athome.templates_managers.copier.copier.run_update') as mock_update:
            engine.update(dest)
        assert mock_update.call_args[0][0] == str(dest)

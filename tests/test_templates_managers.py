"""Tests for TemplateEngine implementations — CopierEngine and CookieCutterEngine."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from athome.definitions.managers.template import TemplateEngine
from athome.templates.managers.cookiecutter import CookieCutterEngine
from athome.templates.managers.copier import CopierEngine

# ---------------------------------------------------------------------------
# CopierEngine
# ---------------------------------------------------------------------------


class TestCopierEngineContract:
    def test_is_template_engine(self) -> None:
        assert issubclass(CopierEngine, TemplateEngine)

    def test_instantiates(self) -> None:
        assert isinstance(CopierEngine(), CopierEngine)


class TestCopierCreate:
    def test_calls_run_copy(self) -> None:
        engine = CopierEngine()
        with patch('athome.templates.managers.copier.copier.run_copy') as mock_copy:
            engine.create('https://example.com/template', Path('/dest'))
        mock_copy.assert_called_once()

    def test_passes_url_as_first_arg(self) -> None:
        engine = CopierEngine()
        url = 'https://github.com/org/template'
        with patch('athome.templates.managers.copier.copier.run_copy') as mock_copy:
            engine.create(url, Path('/dest'))
        assert mock_copy.call_args[0][0] == url

    def test_passes_destination_as_string(self) -> None:
        engine = CopierEngine()
        dest = Path('/my/project')
        with patch('athome.templates.managers.copier.copier.run_copy') as mock_copy:
            engine.create('https://example.com/t', dest)
        assert mock_copy.call_args[0][1] == str(dest)

    def test_forwards_data_and_trust(self) -> None:
        engine = CopierEngine()
        with patch('athome.templates.managers.copier.copier.run_copy') as mock_copy:
            engine.create('https://example.com/t', Path('/dest'), data={'name': 'x'}, trust=True)
        assert mock_copy.call_args.kwargs['data'] == {'name': 'x'}
        assert mock_copy.call_args.kwargs['unsafe'] is True

    def test_defaults_data_none_and_trust_false(self) -> None:
        engine = CopierEngine()
        with patch('athome.templates.managers.copier.copier.run_copy') as mock_copy:
            engine.create('https://example.com/t', Path('/dest'))
        assert mock_copy.call_args.kwargs['data'] is None
        assert mock_copy.call_args.kwargs['unsafe'] is False


class TestCopierUpdate:
    def test_calls_run_update(self) -> None:
        engine = CopierEngine()
        with patch('athome.templates.managers.copier.copier.run_update') as mock_update:
            engine.update(Path('/my/project'))
        mock_update.assert_called_once()

    def test_passes_destination_as_string(self) -> None:
        engine = CopierEngine()
        dest = Path('/my/project')
        with patch('athome.templates.managers.copier.copier.run_update') as mock_update:
            engine.update(dest)
        assert mock_update.call_args[0][0] == str(dest)

    def test_forwards_data_and_trust(self) -> None:
        engine = CopierEngine()
        with patch('athome.templates.managers.copier.copier.run_update') as mock_update:
            engine.update(Path('/my/project'), data={'name': 'x'}, trust=True)
        assert mock_update.call_args.kwargs['data'] == {'name': 'x'}
        assert mock_update.call_args.kwargs['unsafe'] is True


class TestCopierIsInitialized:
    def test_true_when_answers_file_present(self, tmp_path: Path) -> None:
        (tmp_path / '.copier-answers.yml').write_text('_src_path: x\n')
        assert CopierEngine().is_initialized(tmp_path) is True

    def test_false_when_answers_file_absent(self, tmp_path: Path) -> None:
        assert CopierEngine().is_initialized(tmp_path) is False


# ---------------------------------------------------------------------------
# CookieCutterEngine
# ---------------------------------------------------------------------------


class TestCookieCutterEngineContract:
    def test_is_template_engine(self) -> None:
        assert issubclass(CookieCutterEngine, TemplateEngine)

    def test_instantiates(self) -> None:
        assert isinstance(CookieCutterEngine(), CookieCutterEngine)


class TestCookieCutterCreate:
    def test_calls_cruft_create(self) -> None:
        engine = CookieCutterEngine()
        with patch('athome.templates.managers.cookiecutter.cruft.create') as mock_create:
            engine.create('https://example.com/template', Path('/dest'))
        mock_create.assert_called_once()

    def test_passes_template_url(self) -> None:
        engine = CookieCutterEngine()
        url = 'https://github.com/org/cookiecutter-template'
        with patch('athome.templates.managers.cookiecutter.cruft.create') as mock_create:
            engine.create(url, Path('/dest'))
        assert mock_create.call_args[1]['template_git_url'] == url

    def test_passes_output_dir(self) -> None:
        engine = CookieCutterEngine()
        dest = Path('/my/project')
        with patch('athome.templates.managers.cookiecutter.cruft.create') as mock_create:
            engine.create('https://example.com/t', dest)
        assert mock_create.call_args[1]['output_dir'] == dest

    def test_forwards_data_as_extra_context(self) -> None:
        engine = CookieCutterEngine()
        with patch('athome.templates.managers.cookiecutter.cruft.create') as mock_create:
            engine.create('https://example.com/t', Path('/dest'), data={'name': 'x'})
        assert mock_create.call_args.kwargs['extra_context'] == {'name': 'x'}

    def test_trust_flag_accepted_without_error(self) -> None:
        engine = CookieCutterEngine()
        with patch('athome.templates.managers.cookiecutter.cruft.create') as mock_create:
            engine.create('https://example.com/t', Path('/dest'), trust=True)
        mock_create.assert_called_once()


class TestCookieCutterUpdate:
    def test_calls_cruft_update(self) -> None:
        engine = CookieCutterEngine()
        with patch('athome.templates.managers.cookiecutter.cruft.update') as mock_update:
            engine.update(Path('/my/project'))
        mock_update.assert_called_once()

    def test_passes_project_dir(self) -> None:
        engine = CookieCutterEngine()
        dest = Path('/my/project')
        with patch('athome.templates.managers.cookiecutter.cruft.update') as mock_update:
            engine.update(dest)
        assert mock_update.call_args[1]['project_dir'] == dest

    def test_forwards_data_as_extra_context(self) -> None:
        engine = CookieCutterEngine()
        with patch('athome.templates.managers.cookiecutter.cruft.update') as mock_update:
            engine.update(Path('/my/project'), data={'name': 'x'})
        assert mock_update.call_args.kwargs['extra_context'] == {'name': 'x'}


class TestCookieCutterIsInitialized:
    def test_true_when_cruft_json_present(self, tmp_path: Path) -> None:
        (tmp_path / '.cruft.json').write_text('{}')
        assert CookieCutterEngine().is_initialized(tmp_path) is True

    def test_false_when_cruft_json_absent(self, tmp_path: Path) -> None:
        assert CookieCutterEngine().is_initialized(tmp_path) is False

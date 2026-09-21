"""Tests for `athome cleanup` and its supporting athome.tools.cleanup helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

from typer.testing import CliRunner

from athome.cli.main import app
from athome.definitions.config import AthomeConfig
from athome.definitions.config import ProfileConfig
from athome.profiles.managers.chezmoi import ChezmoiManager
from athome.tools.cleanup import build_combined_brewfile
from athome.tools.cleanup import collect_brew_fragments
from athome.tools.cleanup import run_mise_prune

runner = CliRunner()

_CFG = AthomeConfig(
    profiles={'work': ProfileConfig(name='work', source='https://github.com/org/dotfiles-work')},
)
_EMPTY_CFG = AthomeConfig()


def _write_brewfile(profile_root: Path, name: str, content: str) -> None:
    file_d = profile_root / 'dot_config' / 'brew' / 'file.d'
    file_d.mkdir(parents=True, exist_ok=True)
    (file_d / f'{name}.Brewfile').write_text(content)


# ---------------------------------------------------------------------------
# athome.tools.cleanup helpers
# ---------------------------------------------------------------------------


class TestCollectBrewFragments:
    def test_collects_fragment_content(self, tmp_path: Path) -> None:
        source = tmp_path / 'work'
        _write_brewfile(source, 'work', 'brew "git"\n')
        profile = ProfileConfig(name='work', source='url', destination=source)
        chezmoi = MagicMock(spec=ChezmoiManager)

        fragments = collect_brew_fragments(chezmoi, {'work': profile})

        assert fragments == [('work/work.Brewfile', 'brew "git"\n')]
        chezmoi.render_template.assert_not_called()

    def test_renders_tmpl_fragments_via_chezmoi(self, tmp_path: Path) -> None:
        source = tmp_path / 'work'
        file_d = source / 'dot_config' / 'brew' / 'file.d'
        file_d.mkdir(parents=True)
        (file_d / 'work.Brewfile.tmpl').write_text('brew "{{ .name }}"\n')
        profile = ProfileConfig(name='work', source='url', destination=source)
        chezmoi = MagicMock(spec=ChezmoiManager)
        chezmoi.render_template.return_value = 'brew "git"\n'

        fragments = collect_brew_fragments(chezmoi, {'work': profile})

        assert fragments == [('work/work.Brewfile.tmpl', 'brew "git"\n')]
        chezmoi.render_template.assert_called_once()

    def test_collects_from_chezmoiroot_subdirectory(self, tmp_path: Path) -> None:
        """A profile repo using `.chezmoiroot` keeps its fragments one level down.

        Globbing the checkout root instead finds nothing, which silently reports
        an empty declared set — and `brew bundle cleanup` against an empty
        manifest means every installed package looks undeclared.
        """
        checkout = tmp_path / 'work'
        checkout.mkdir()
        (checkout / '.chezmoiroot').write_text('chezmoi\n')
        _write_brewfile(checkout / 'chezmoi', 'work', 'brew "git"\n')
        profile = ProfileConfig(name='work', source='url', destination=checkout)
        chezmoi = MagicMock(spec=ChezmoiManager)

        fragments = collect_brew_fragments(chezmoi, {'work': profile})

        assert fragments == [('work/work.Brewfile', 'brew "git"\n')]

    def test_ignores_fragments_left_at_the_checkout_root(self, tmp_path: Path) -> None:
        """With `.chezmoiroot` set, the checkout root is not the source tree."""
        checkout = tmp_path / 'work'
        checkout.mkdir()
        (checkout / '.chezmoiroot').write_text('chezmoi\n')
        (checkout / 'chezmoi').mkdir()
        _write_brewfile(checkout, 'stray', 'brew "stray"\n')
        profile = ProfileConfig(name='work', source='url', destination=checkout)
        chezmoi = MagicMock(spec=ChezmoiManager)

        assert collect_brew_fragments(chezmoi, {'work': profile}) == []

    def test_no_fragments_yields_empty_list(self, tmp_path: Path) -> None:
        source = tmp_path / 'work'
        source.mkdir()
        profile = ProfileConfig(name='work', source='url', destination=source)
        chezmoi = MagicMock(spec=ChezmoiManager)

        assert collect_brew_fragments(chezmoi, {'work': profile}) == []

    def test_collects_across_profiles(self, tmp_path: Path) -> None:
        work_source = tmp_path / 'work'
        personal_source = tmp_path / 'personal'
        _write_brewfile(work_source, 'work', 'brew "git"\n')
        _write_brewfile(personal_source, 'personal', 'brew "htop"\n')
        profiles = {
            'work': ProfileConfig(name='work', source='url', destination=work_source),
            'personal': ProfileConfig(name='personal', source='url', destination=personal_source),
        }
        chezmoi = MagicMock(spec=ChezmoiManager)

        fragments = collect_brew_fragments(chezmoi, profiles)

        assert len(fragments) == 2
        labels = {label for label, _ in fragments}
        assert labels == {'work/work.Brewfile', 'personal/personal.Brewfile'}


class TestBuildCombinedBrewfile:
    def test_labels_each_fragment(self) -> None:
        combined = build_combined_brewfile([('work/a.Brewfile', 'brew "git"')])
        assert '# --- work/a.Brewfile ---' in combined
        assert 'brew "git"' in combined

    def test_joins_multiple_fragments(self) -> None:
        combined = build_combined_brewfile([
            ('a.Brewfile', 'brew "git"'),
            ('b.Brewfile', 'brew "htop"'),
        ])
        assert 'brew "git"' in combined
        assert 'brew "htop"' in combined

    def test_empty_list_yields_empty_string(self) -> None:
        assert build_combined_brewfile([]) == ''


class TestRunMisePrune:
    def test_default_is_dry_run(self) -> None:
        with patch('athome.tools.cleanup.subprocess.run') as mock_run:
            run_mise_prune()
        assert mock_run.call_args[0][0] == ['mise', 'prune', '--dry-run']

    def test_force_uses_yes_flag(self) -> None:
        with patch('athome.tools.cleanup.subprocess.run') as mock_run:
            run_mise_prune(force=True)
        assert mock_run.call_args[0][0] == ['mise', 'prune', '-y']


# ---------------------------------------------------------------------------
# `athome cleanup` command
# ---------------------------------------------------------------------------


class TestCleanupCommand:
    def test_no_profiles_exits_one(self) -> None:
        with patch('athome.cli.cleanup.load_config', return_value=_EMPTY_CFG):
            result = runner.invoke(app, ['cleanup'])
        assert result.exit_code == 1

    def test_no_brew_fragments_skips_brew_bundle(self) -> None:
        with (
            patch('athome.cli.cleanup.load_config', return_value=_CFG),
            patch('athome.cli.cleanup.collect_brew_fragments', return_value=[]),
            patch('athome.cli.cleanup.shutil.which', return_value='/usr/bin/mise'),
            patch('athome.cli.cleanup.run_mise_prune') as mock_prune,
        ):
            result = runner.invoke(app, ['cleanup'])
        assert result.exit_code == 0
        assert 'No Brewfile fragments' in result.output
        mock_prune.assert_called_once()

    def test_brew_missing_prints_warning(self) -> None:
        def which(tool: str) -> str | None:
            return None if tool == 'brew' else f'/usr/bin/{tool}'

        with (
            patch('athome.cli.cleanup.load_config', return_value=_CFG),
            patch(
                'athome.cli.cleanup.collect_brew_fragments',
                return_value=[('work/a.Brewfile', 'brew "git"')],
            ),
            patch('athome.cli.cleanup.shutil.which', side_effect=which),
        ):
            result = runner.invoke(app, ['cleanup', '--skip-mise'])
        assert result.exit_code == 0
        assert 'brew is not installed' in result.stderr

    def test_runs_brew_bundle_cleanup_with_combined_manifest(self, tmp_path: Path) -> None:
        with (
            patch('athome.cli.cleanup.load_config', return_value=_CFG),
            patch(
                'athome.cli.cleanup.collect_brew_fragments',
                return_value=[('work/a.Brewfile', 'brew "git"')],
            ),
            patch('athome.cli.cleanup.shutil.which', return_value='/usr/local/bin/brew'),
            patch('athome.cli.cleanup.BrewManager') as mock_brew_cls,
        ):
            result = runner.invoke(app, ['cleanup', '--skip-mise'])
        assert result.exit_code == 0
        mock_brew_cls.return_value.cleanup.assert_called_once()
        manifest_path = mock_brew_cls.return_value.cleanup.call_args[0][0]
        assert not manifest_path.exists()  # temp file cleaned up

    def test_force_flag_passed_to_brew_cleanup(self) -> None:
        with (
            patch('athome.cli.cleanup.load_config', return_value=_CFG),
            patch(
                'athome.cli.cleanup.collect_brew_fragments',
                return_value=[('work/a.Brewfile', 'brew "git"')],
            ),
            patch('athome.cli.cleanup.shutil.which', return_value='/usr/local/bin/brew'),
            patch('athome.cli.cleanup.BrewManager') as mock_brew_cls,
        ):
            runner.invoke(app, ['cleanup', '--force', '--skip-mise'])
        assert mock_brew_cls.return_value.cleanup.call_args[1]['force'] is True

    def test_skip_brew_skips_brew_entirely(self) -> None:
        with (
            patch('athome.cli.cleanup.load_config', return_value=_CFG),
            patch('athome.cli.cleanup.collect_brew_fragments') as mock_collect,
            patch('athome.cli.cleanup.shutil.which', return_value='/usr/bin/mise'),
            patch('athome.cli.cleanup.run_mise_prune'),
        ):
            result = runner.invoke(app, ['cleanup', '--skip-brew'])
        assert result.exit_code == 0
        mock_collect.assert_not_called()

    def test_mise_missing_prints_warning(self) -> None:
        with (
            patch('athome.cli.cleanup.load_config', return_value=_CFG),
            patch('athome.cli.cleanup.shutil.which', return_value=None),
        ):
            result = runner.invoke(app, ['cleanup', '--skip-brew'])
        assert result.exit_code == 0
        assert 'mise is not installed' in result.stderr

    def test_runs_mise_prune(self) -> None:
        with (
            patch('athome.cli.cleanup.load_config', return_value=_CFG),
            patch('athome.cli.cleanup.shutil.which', return_value='/usr/bin/mise'),
            patch('athome.cli.cleanup.run_mise_prune') as mock_prune,
        ):
            result = runner.invoke(app, ['cleanup', '--skip-brew', '--force'])
        assert result.exit_code == 0
        mock_prune.assert_called_once_with(force=True)

    def test_skip_mise_skips_mise_entirely(self) -> None:
        with (
            patch('athome.cli.cleanup.load_config', return_value=_CFG),
            patch('athome.cli.cleanup.collect_brew_fragments', return_value=[]),
            patch('athome.cli.cleanup.run_mise_prune') as mock_prune,
        ):
            result = runner.invoke(app, ['cleanup', '--skip-mise'])
        assert result.exit_code == 0
        mock_prune.assert_not_called()

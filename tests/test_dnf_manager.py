"""Tests for DnfManager — the dnf-in-a-dev-box tool manager."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

import pytest

from athome.exceptions import ToolNotFoundError
from athome.tools.managers.dnf import DnfManager

_BASE_PATCH = 'athome.definitions.managers.base.shutil.which'
_RUN = 'athome.tools.managers.dnf.subprocess.run'


def _completed(stdout: str = '', returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr='')


@pytest.fixture
def distrobox_available() -> object:
    with patch(_BASE_PATCH, return_value='/usr/bin/distrobox'):
        yield


class TestDnfSync:
    def test_no_packages_runs_nothing(self, distrobox_available: None) -> None:
        with patch(_RUN) as run:
            DnfManager().sync('dev', [])
        run.assert_not_called()

    def test_installs_declared_packages(self, distrobox_available: None) -> None:
        # baseline already recorded, so ensure_baseline short-circuits
        with patch(_RUN, return_value=_completed('gcc\n')) as run:
            DnfManager().sync('dev', ['libpq-devel', 'portaudio-devel'])
        cmd = run.call_args[0][0]
        assert cmd == [
            'distrobox',
            'enter',
            'dev',
            '--',
            'sudo',
            'dnf',
            'install',
            '-y',
            'libpq-devel',
            'portaudio-devel',
        ]


class TestDnfBaseline:
    def test_existing_baseline_is_not_rewritten(self, distrobox_available: None) -> None:
        """Re-recording would fold our own packages in and make them unremovable."""
        with patch(_RUN, return_value=_completed('gcc\nmake\n')) as run:
            baseline = DnfManager().ensure_baseline('dev')
        assert baseline == {'gcc', 'make'}
        # only the `cat` probe ran — no tee, no mkdir
        assert run.call_count == 1

    def test_absent_baseline_is_recorded_from_current_state(
        self, distrobox_available: None
    ) -> None:
        outcomes = [
            _completed('', returncode=1),  # cat: no baseline yet
            _completed('gcc\nmake\n'),  # repoquery --userinstalled
            _completed(''),  # mkdir -p
            _completed(''),  # tee
        ]
        with patch(_RUN, side_effect=outcomes) as run:
            baseline = DnfManager().ensure_baseline('dev')
        assert baseline == {'gcc', 'make'}
        assert any('tee' in call[0][0] for call in run.call_args_list)


class TestDnfQueryFormat:
    def test_repoquery_format_is_newline_terminated(self, distrobox_available: None) -> None:
        """Without the trailing newline dnf emits one concatenated blob.

        The parsed set then holds a single giant entry, every real package looks
        like it belongs to the base image, and cleanup silently reports nothing
        to remove.
        """
        outcomes = [
            _completed('', returncode=1),  # cat: no baseline yet
            _completed('gcc\n'),  # repoquery
            _completed(''),  # mkdir -p
            _completed(''),  # tee
        ]
        with patch(_RUN, side_effect=outcomes) as run:
            DnfManager().ensure_baseline('dev')
        query = next(c[0][0] for c in run.call_args_list if 'repoquery' in c[0][0])
        assert query[-1].endswith('\n')


class TestDnfRemovable:
    def test_image_packages_are_never_proposed(self, distrobox_available: None) -> None:
        """The base image is 'userinstalled' too — reconciling naively would eat it."""
        with patch(_RUN, return_value=_completed('gcc\nmake\nbash\n')):
            extra = DnfManager().removable('dev', declared=set())
        assert extra == []

    def test_undeclared_additions_are_proposed(self, distrobox_available: None) -> None:
        outcomes = [
            _completed('gcc\nmake\n'),  # cat baseline
            _completed('gcc\nmake\nlibpq-devel\nportaudio-devel\n'),  # userinstalled now
        ]
        with patch(_RUN, side_effect=outcomes):
            extra = DnfManager().removable('dev', declared={'libpq-devel'})
        assert extra == ['portaudio-devel']


class TestDnfCleanup:
    def test_dry_run_lists_without_removing(self, distrobox_available: None) -> None:
        outcomes = [_completed('gcc\n'), _completed('gcc\nvim\n')]
        with patch(_RUN, side_effect=outcomes) as run:
            extra = DnfManager().cleanup('dev', declared=set(), force=False)
        assert extra == ['vim']
        assert not any('remove' in call[0][0] for call in run.call_args_list)

    def test_force_removes(self, distrobox_available: None) -> None:
        outcomes = [_completed('gcc\n'), _completed('gcc\nvim\n'), _completed('')]
        with patch(_RUN, side_effect=outcomes) as run:
            extra = DnfManager().cleanup('dev', declared=set(), force=True)
        assert extra == ['vim']
        assert any('remove' in call[0][0] for call in run.call_args_list)


class TestDnfToolNotFound:
    def test_instantiation_never_raises_when_distrobox_missing(self) -> None:
        with patch(_BASE_PATCH, return_value=None):
            DnfManager()

    def test_sync_raises_when_distrobox_missing(self) -> None:
        with patch(_BASE_PATCH, return_value=None), pytest.raises(ToolNotFoundError):
            DnfManager().sync('dev', ['gcc'])

"""Tests for athome.backup utilities."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from athome.profiles.backup import backup_files
from athome.profiles.backup import default_backup_name


class TestDefaultBackupName:
    def test_contains_profile_name(self) -> None:
        name = default_backup_name('work')
        assert 'work' in name

    def test_contains_timestamp_prefix(self) -> None:
        name = default_backup_name('work')
        assert name.startswith('backup-before-apply-work_')

    def test_different_calls_can_produce_same_second(self) -> None:
        from datetime import datetime

        fixed = datetime(2026, 6, 2, 14, 30, 0)
        with patch('athome.backup.datetime') as mock_dt:
            mock_dt.now.return_value = fixed
            name = default_backup_name('personal')
        assert name == 'backup-before-apply-personal_2026-06-02_14-30-00'


class TestBackupFiles:
    def test_copies_existing_file(self, tmp_path: Path) -> None:
        src = tmp_path / 'home' / '.bashrc'
        src.parent.mkdir(parents=True)
        src.write_text('alias ll=ls')
        backup_dir = tmp_path / 'backup'

        with patch('athome.backup.Path.home', return_value=tmp_path / 'home'):
            backup_files([src], backup_dir)

        assert (backup_dir / '.bashrc').read_text() == 'alias ll=ls'

    def test_preserves_home_relative_structure(self, tmp_path: Path) -> None:
        home = tmp_path / 'home'
        src = home / '.config' / 'nvim' / 'init.lua'
        src.parent.mkdir(parents=True)
        src.write_text('return {}')
        backup_dir = tmp_path / 'backup'

        with patch('athome.backup.Path.home', return_value=home):
            backup_files([src], backup_dir)

        assert (backup_dir / '.config' / 'nvim' / 'init.lua').exists()

    def test_skips_missing_files(self, tmp_path: Path) -> None:
        missing = tmp_path / 'nonexistent'
        backup_dir = tmp_path / 'backup'
        count = backup_files([missing], backup_dir)
        assert count == 0
        assert not backup_dir.exists()

    def test_returns_count_of_copied_files(self, tmp_path: Path) -> None:
        home = tmp_path / 'home'
        files = [home / f'.file{i}' for i in range(3)]
        for f in files:
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text('x')
        backup_dir = tmp_path / 'backup'

        with patch('athome.backup.Path.home', return_value=home):
            count = backup_files(files, backup_dir)

        assert count == 3

    def test_files_outside_home_stored_flat(self, tmp_path: Path) -> None:
        src = tmp_path / 'etc' / 'hosts'
        src.parent.mkdir()
        src.write_text('127.0.0.1 localhost')
        backup_dir = tmp_path / 'backup'
        home = tmp_path / 'home'

        with patch('athome.backup.Path.home', return_value=home):
            backup_files([src], backup_dir)

        assert (backup_dir / 'hosts').exists()

    def test_empty_list_does_nothing(self, tmp_path: Path) -> None:
        backup_dir = tmp_path / 'backup'
        count = backup_files([], backup_dir)
        assert count == 0
        assert not backup_dir.exists()

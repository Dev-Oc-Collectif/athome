"""Tests for the profile stack orchestrator."""

from __future__ import annotations

from pathlib import Path

from athome.definitions.config import ProfileConfig
from athome.profiles.orchestrator import AthomeState
from athome.profiles.orchestrator import compute_switch
from athome.profiles.orchestrator import load_state
from athome.profiles.orchestrator import resolve_stack
from athome.profiles.orchestrator import save_state

_PROFILES: dict[str, ProfileConfig] = {
    'base': ProfileConfig(name='base', source='url-base', loads=[]),
    'work': ProfileConfig(name='work', source='url-work', loads=['base']),
    'personal': ProfileConfig(name='personal', source='url-personal', loads=[]),
    'setup-remote': ProfileConfig(name='setup-remote', source='url-remote', loads=['base', 'work']),
}


class TestResolveStack:
    def test_profile_with_no_loads(self) -> None:
        result = resolve_stack('base', _PROFILES)
        assert result == ['base']

    def test_profile_includes_its_deps_first(self) -> None:
        result = resolve_stack('work', _PROFILES)
        assert result.index('base') < result.index('work')

    def test_all_deps_included(self) -> None:
        result = resolve_stack('setup-remote', _PROFILES)
        assert set(result) >= {'base', 'work', 'setup-remote'}

    def test_no_duplicates(self) -> None:
        result = resolve_stack('setup-remote', _PROFILES)
        assert len(result) == len(set(result))

    def test_unknown_profile_returns_name_only(self) -> None:
        result = resolve_stack('ghost', _PROFILES)
        assert result == ['ghost']

    def test_cycle_does_not_hang(self) -> None:
        cyclic: dict[str, ProfileConfig] = {
            'a': ProfileConfig(name='a', source='url', loads=['b']),
            'b': ProfileConfig(name='b', source='url', loads=['a']),
        }
        result = resolve_stack('a', cyclic)
        assert 'a' in result
        assert 'b' in result


class TestComputeSwitch:
    def test_nothing_to_do_when_stacks_equal(self) -> None:
        to_unapply, to_apply, remaining = compute_switch(['base', 'work'], ['base', 'work'])
        assert to_unapply == []
        assert to_apply == []
        assert remaining == {'base', 'work'}

    def test_profiles_to_remove_are_in_to_unapply(self) -> None:
        to_unapply, _, _ = compute_switch(['base', 'work'], ['base'])
        assert 'work' in to_unapply
        assert 'base' not in to_unapply

    def test_profiles_to_add_are_in_to_apply(self) -> None:
        _, to_apply, _ = compute_switch(['base'], ['base', 'personal'])
        assert 'personal' in to_apply
        assert 'base' not in to_apply

    def test_remaining_profiles_in_both_stacks(self) -> None:
        _, _, remaining = compute_switch(['base', 'work'], ['base', 'personal'])
        assert remaining == {'base'}

    def test_unapply_order_is_reversed(self) -> None:
        to_unapply, _, _ = compute_switch(['base', 'work', 'setup-remote'], ['personal'])
        assert to_unapply[0] == 'setup-remote'
        assert to_unapply[-1] == 'base'


class TestLoadSaveState:
    def test_load_returns_empty_state_when_file_absent(self, tmp_path: Path) -> None:
        state = load_state(tmp_path / 'nonexistent.toml')
        assert state.active_profiles == []

    def test_save_then_load_roundtrip(self, tmp_path: Path) -> None:
        path = tmp_path / 'state.toml'
        original = AthomeState(active_profiles=['base', 'work'])
        save_state(original, path)
        loaded = load_state(path)
        assert loaded.active_profiles == ['base', 'work']

    def test_save_creates_parent_dirs(self, tmp_path: Path) -> None:
        path = tmp_path / 'nested' / 'dir' / 'state.toml'
        save_state(AthomeState(), path)
        assert path.exists()

    def test_empty_active_profiles(self, tmp_path: Path) -> None:
        path = tmp_path / 'state.toml'
        save_state(AthomeState(active_profiles=[]), path)
        loaded = load_state(path)
        assert loaded.active_profiles == []

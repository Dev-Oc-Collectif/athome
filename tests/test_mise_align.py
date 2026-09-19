"""Tests for athome.tools.mise_align — cross-profile mise version drift detection."""

from __future__ import annotations

from pathlib import Path

from athome.definitions.config import ProfileConfig
from athome.tools.mise_align import collect_tool_versions
from athome.tools.mise_align import find_drift


def _write_conf_d(profile_root: Path, name: str, content: str) -> None:
    conf_d = profile_root / 'dot_config' / 'mise' / 'conf.d'
    conf_d.mkdir(parents=True, exist_ok=True)
    (conf_d / f'{name}.toml').write_text(content)


class TestCollectToolVersions:
    def test_collects_single_profile_single_tool(self, tmp_path: Path) -> None:
        source = tmp_path / 'work'
        _write_conf_d(source, 'work', '[tools]\nnode = "20"\n')
        profile = ProfileConfig(name='work', source='url', destination=source)

        result = collect_tool_versions({'work': profile})

        assert result == {'node': {'work': '20'}}

    def test_collects_from_chezmoiroot_subdirectory(self, tmp_path: Path) -> None:
        """Same `.chezmoiroot` re-rooting as the brew side — otherwise drift
        between profiles is silently never detected."""
        checkout = tmp_path / 'work'
        checkout.mkdir()
        (checkout / '.chezmoiroot').write_text('chezmoi\n')
        _write_conf_d(checkout / 'chezmoi', 'work', '[tools]\nnode = "20"\n')
        profile = ProfileConfig(name='work', source='url', destination=checkout)

        assert collect_tool_versions({'work': profile}) == {'node': {'work': '20'}}

    def test_merges_multiple_fragments_in_same_profile(self, tmp_path: Path) -> None:
        source = tmp_path / 'work'
        _write_conf_d(source, 'a', '[tools]\nnode = "20"\n')
        _write_conf_d(source, 'b', '[tools]\npython = "3.12"\n')
        profile = ProfileConfig(name='work', source='url', destination=source)

        result = collect_tool_versions({'work': profile})

        assert result == {'node': {'work': '20'}, 'python': {'work': '3.12'}}

    def test_collects_across_profiles(self, tmp_path: Path) -> None:
        work_source = tmp_path / 'work'
        personal_source = tmp_path / 'personal'
        _write_conf_d(work_source, 'work', '[tools]\nnode = "20"\n')
        _write_conf_d(personal_source, 'personal', '[tools]\nnode = "22"\n')
        profiles = {
            'work': ProfileConfig(name='work', source='url', destination=work_source),
            'personal': ProfileConfig(name='personal', source='url', destination=personal_source),
        }

        result = collect_tool_versions(profiles)

        assert result == {'node': {'work': '20', 'personal': '22'}}

    def test_no_fragments_yields_empty(self, tmp_path: Path) -> None:
        source = tmp_path / 'work'
        source.mkdir()
        profile = ProfileConfig(name='work', source='url', destination=source)

        assert collect_tool_versions({'work': profile}) == {}

    def test_missing_profile_dir_yields_empty(self, tmp_path: Path) -> None:
        profile = ProfileConfig(name='work', source='url', destination=tmp_path / 'missing')

        assert collect_tool_versions({'work': profile}) == {}

    def test_normalizes_table_version_spec(self, tmp_path: Path) -> None:
        source = tmp_path / 'work'
        _write_conf_d(source, 'work', '[tools]\nnode = {version = "20"}\n')
        profile = ProfileConfig(name='work', source='url', destination=source)

        result = collect_tool_versions({'work': profile})

        assert result == {'node': {'work': '20'}}

    def test_normalizes_list_version_spec(self, tmp_path: Path) -> None:
        source = tmp_path / 'work'
        _write_conf_d(source, 'work', '[tools]\nnode = ["20", "18"]\n')
        profile = ProfileConfig(name='work', source='url', destination=source)

        result = collect_tool_versions({'work': profile})

        assert result == {'node': {'work': '18,20'}}


class TestFindDrift:
    def test_no_drift_when_versions_match(self, tmp_path: Path) -> None:
        work_source = tmp_path / 'work'
        personal_source = tmp_path / 'personal'
        _write_conf_d(work_source, 'work', '[tools]\nnode = "20"\n')
        _write_conf_d(personal_source, 'personal', '[tools]\nnode = "20"\n')
        profiles = {
            'work': ProfileConfig(name='work', source='url', destination=work_source),
            'personal': ProfileConfig(name='personal', source='url', destination=personal_source),
        }

        assert find_drift(profiles) == []

    def test_detects_drift_across_profiles(self, tmp_path: Path) -> None:
        work_source = tmp_path / 'work'
        personal_source = tmp_path / 'personal'
        _write_conf_d(work_source, 'work', '[tools]\nnode = "20"\n')
        _write_conf_d(personal_source, 'personal', '[tools]\nnode = "22"\n')
        profiles = {
            'work': ProfileConfig(name='work', source='url', destination=work_source),
            'personal': ProfileConfig(name='personal', source='url', destination=personal_source),
        }

        drifts = find_drift(profiles)

        assert len(drifts) == 1
        assert drifts[0].tool == 'node'
        assert drifts[0].versions == {'work': '20', 'personal': '22'}

    def test_single_profile_never_drifts(self, tmp_path: Path) -> None:
        source = tmp_path / 'work'
        _write_conf_d(source, 'work', '[tools]\nnode = "20"\n')
        profile = ProfileConfig(name='work', source='url', destination=source)

        assert find_drift({'work': profile}) == []

    def test_only_drifting_tools_are_reported(self, tmp_path: Path) -> None:
        work_source = tmp_path / 'work'
        personal_source = tmp_path / 'personal'
        _write_conf_d(work_source, 'work', '[tools]\nnode = "20"\npython = "3.12"\n')
        _write_conf_d(personal_source, 'personal', '[tools]\nnode = "22"\npython = "3.12"\n')
        profiles = {
            'work': ProfileConfig(name='work', source='url', destination=work_source),
            'personal': ProfileConfig(name='personal', source='url', destination=personal_source),
        }

        drifts = find_drift(profiles)

        assert [d.tool for d in drifts] == ['node']

"""Cross-profile cleanup — reconcile installed brew/mise state against every configured profile.

The brew side aggregates every profile's Brewfile fragments into one combined
manifest (profiles aren't necessarily all "active"/applied at once, so this is
the only way to see the full declared set). The mise side does not: mise's own
config resolution already merges every *currently applied* profile's conf.d
fragment from the real `~/.config/mise/conf.d/`, and — confirmed by testing —
`mise prune` also always consults that real global location internally
regardless of any `MISE_CONFIG_DIR` override, so synthesizing an isolated
config directory for it doesn't actually isolate anything; it just adds
complexity on top of what `mise prune` already does correctly on its own.
"""

from __future__ import annotations

import subprocess  # nosec
from pathlib import Path
from typing import TYPE_CHECKING

from athome.definitions.config import ProfileConfig
from athome.definitions.config import profile_source_root

if TYPE_CHECKING:
    from athome.profiles.managers.chezmoi import ChezmoiManager

BREW_FILED_DIR = 'dot_config/brew/file.d'
DEVBOX_PKGD_DIR = 'dot_config/devbox/pkg.d'


def _render(chezmoi: ChezmoiManager, profile: ProfileConfig, fragment: Path) -> str:
    if fragment.suffix == '.tmpl':
        return chezmoi.render_template(profile, fragment)
    return fragment.read_text()


def _collect_fragments(
    chezmoi: ChezmoiManager,
    profiles: dict[str, ProfileConfig],
    subdir: str,
    suffix: str,
) -> list[tuple[str, str]]:
    """Return [(label, rendered_content), ...] for every matching fragment, sorted."""
    fragments: list[tuple[str, str]] = []
    for profile in profiles.values():
        source = profile_source_root(profile)
        paths = sorted(source.glob(f'{subdir}/*{suffix}')) + sorted(
            source.glob(f'{subdir}/*{suffix}.tmpl')
        )
        for path in paths:
            label = f'{profile.name}/{path.name}'
            fragments.append((label, _render(chezmoi, profile, path)))
    return fragments


def collect_brew_fragments(
    chezmoi: ChezmoiManager, profiles: dict[str, ProfileConfig]
) -> list[tuple[str, str]]:
    """Return every Brewfile fragment across configured profiles."""
    return _collect_fragments(chezmoi, profiles, BREW_FILED_DIR, '.Brewfile')


def collect_devbox_packages(
    chezmoi: ChezmoiManager, profiles: dict[str, ProfileConfig]
) -> set[str]:
    """Return every dnf package declared across configured profiles.

    Fragments are plain lists, one package per line, `#` for comments — the
    same shape as the Brewfile fragments, using the dev box's native manager.
    """
    packages: set[str] = set()
    for _label, content in _collect_fragments(chezmoi, profiles, DEVBOX_PKGD_DIR, '.dnf'):
        for raw in content.splitlines():
            line = raw.split('#', 1)[0].strip()
            if line:
                packages.add(line)
    return packages


def build_combined_brewfile(fragments: list[tuple[str, str]]) -> str:
    """Concatenate Brewfile fragments into one file, labelled by origin."""
    return '\n\n'.join(f'# --- {label} ---\n{content}' for label, content in fragments)


def run_mise_prune(*, force: bool = False) -> None:
    """Run `mise prune` against the real global mise state.

    Reconciles installed tool versions against whatever every currently
    applied profile has deployed to ~/.config/mise/conf.d/ — that's the same
    set `mise` itself already resolves, no aggregation needed on athome's side.
    """
    args = ['mise', 'prune', *(['-y'] if force else ['--dry-run'])]
    subprocess.run(args, check=True)  # noqa: S603 # nosec

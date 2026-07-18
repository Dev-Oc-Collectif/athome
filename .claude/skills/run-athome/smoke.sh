#!/usr/bin/env bash
# smoke.sh — drive the athome CLI and assert expected output / exit codes.
# Run from the repo root: bash .claude/skills/run-athome/smoke.sh
# Requires: .venv already created (uv sync --dev)

set -uo pipefail

PASS=0; FAIL=0

athome() { .venv/bin/athome "$@"; }

# ── helpers ────────────────────────────────────────────────────────────────
ok()   { echo "  ✓  $1"; PASS=$((PASS + 1)); }
fail() { echo "  ✗  $1"; FAIL=$((FAIL + 1)); }

assert_exit() {
    local label="$1" want="$2"; shift 2
    local actual=0
    "$@" > /dev/null 2>&1 || actual=$?
    [ "$actual" -eq "$want" ] && ok "$label (exit $want)" \
                              || fail "$label (want exit $want, got $actual)"
}

assert_output() {
    local label="$1" pattern="$2"; shift 2
    local out
    out=$("$@" 2>&1) || true
    echo "$out" | grep -q "$pattern" && ok "$label" \
                                     || fail "$label — expected '$pattern' in output"
}

# ── fixture config via HOME override ───────────────────────────────────────
FAKEHOME=$(mktemp -d)
NOHOME=$(mktemp -d)
trap 'rm -rf "$FAKEHOME" "$NOHOME"' EXIT

mkdir -p "$FAKEHOME/.config/athome"
cat > "$FAKEHOME/.config/athome/config.toml" <<'TOML'
[profiles]
personal = "https://github.com/your-user/dotfiles-personal"
work     = "https://github.com/your-org/dotfiles-work"

[templates]
python = "https://github.com/Dev-Oc-Collectif/python-template"
zola   = "https://github.com/Dev-Oc-Collectif/zola-template"

[workspace.owners]
my-org = {source = "https://github.com/your-org"}

[workspace.repos]
dotfiles = "https://github.com/your-user/dotfiles"
TOML

echo ""
echo "── help / structure ───────────────────────────────────────────────────"

assert_exit   "root --help"          0  athome --help
assert_output "root lists profile"   "profile"    athome --help
assert_output "root lists repo"      "repo"       athome --help
assert_output "root lists brew"      "brew"       athome --help
assert_output "root lists create"    "create"     athome --help
assert_output "root lists templates" "templates"  athome --help
assert_output "root lists cleanup"   "cleanup"    athome --help

assert_exit "profile --help"  0  athome profile  --help
assert_exit "project --help"  0  athome project  --help
assert_exit "repo --help"     0  athome repo     --help
assert_exit "template --help" 0  athome template --help
assert_exit "brew --help"     0  athome brew     --help
assert_exit "mise --help"     0  athome mise     --help
assert_exit "system --help"   0  athome system   --help
assert_exit "cleanup --help"  0  athome cleanup  --help

echo ""
echo "── no-config graceful messages ────────────────────────────────────────"

assert_output "profile list (empty)" "No profiles defined" \
    env HOME="$NOHOME" .venv/bin/athome profile list
assert_output "template list (empty)" "No templates configured" \
    env HOME="$NOHOME" .venv/bin/athome template list

echo ""
echo "── with fixture config.toml ───────────────────────────────────────────"

assert_output "profile list shows personal" "personal" \
    env HOME="$FAKEHOME" .venv/bin/athome profile list
assert_output "profile list shows work" "work" \
    env HOME="$FAKEHOME" .venv/bin/athome profile list
assert_output "template list shows python" "python" \
    env HOME="$FAKEHOME" .venv/bin/athome template list
assert_output "template list shows zola" "zola" \
    env HOME="$FAKEHOME" .venv/bin/athome template list

echo ""
echo "── unknown profile aborts with exit 1 ────────────────────────────────"

assert_exit "profile sync (unknown name)" 1 \
    env HOME="$NOHOME" .venv/bin/athome profile sync nonexistent

echo ""
echo "── system doctor ──────────────────────────────────────────────────────"

# doctor exits 0 only when all tools are found; on CI some may be missing —
# we assert graceful output regardless of exit code
out=$(athome system doctor 2>&1 || true)
echo "$out" | grep -qE '[✓✗]' && ok "doctor prints tool status" \
                                 || fail "doctor output unexpected: $out"

echo ""
echo "── summary ────────────────────────────────────────────────────────────"
echo "  passed: $PASS   failed: $FAIL"
[ "$FAIL" -eq 0 ]

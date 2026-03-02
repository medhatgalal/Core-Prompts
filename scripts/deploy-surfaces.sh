#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/deploy-surfaces.sh [--cli gemini|claude|kiro|codex|all] [--dry-run] [--strict-cli]

Copy-only deployment of SSOT-managed generated surfaces to home CLI directories.
This script never deletes files and never creates symlinks.
Existing files are overwritten in place with cp -f.

Options:
  --cli gemini|claude|kiro|codex|all  Target CLI(s). Default: all
  --dry-run                           Show copy actions without writing
  --strict-cli                        Fail when selected CLI binary is not installed
  -h, --help                          Show this help
EOF
}

CLI_TARGET="all"
DRY_RUN=0
STRICT_CLI=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --cli)
      shift
      CLI_TARGET="${1:-}"
      ;;
    --dry-run)
      DRY_RUN=1
      ;;
    --strict-cli)
      STRICT_CLI=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown option: $1"
      usage
      exit 1
      ;;
  esac
  shift
done

case "$CLI_TARGET" in
  gemini|claude|kiro|codex|all) ;;
  *)
    echo "error: invalid --cli value: $CLI_TARGET"
    usage
    exit 1
    ;;
esac

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [[ ! -f ".meta/manifest.json" ]]; then
  echo "error: missing .meta/manifest.json"
  echo "Run build first: python3 scripts/build-surfaces.py"
  exit 1
fi

if ! mapfile -t SLUGS < <(python3 - <<'PY'
import json
from pathlib import Path
try:
    manifest = json.loads(Path(".meta/manifest.json").read_text(encoding="utf-8"))
except Exception as exc:
    raise SystemExit(f"manifest_read_error: {exc}")

for entry in manifest.get("ssot_sources", []):
    slug = entry.get("slug")
    if slug:
        print(slug)
PY
); then
  echo "error: unreadable .meta/manifest.json"
  exit 1
fi

if [[ ${#SLUGS[@]} -eq 0 ]]; then
  echo "error: no managed slugs found in .meta/manifest.json"
  exit 1
fi

is_cli_available() {
  local cli="$1"
  case "$cli" in
    gemini) command -v gemini >/dev/null 2>&1 ;;
    claude) command -v claude >/dev/null 2>&1 ;;
    kiro) command -v kiro-cli >/dev/null 2>&1 ;;
    codex) command -v codex >/dev/null 2>&1 ;;
    *) return 1 ;;
  esac
}

TARGETS=()
if [[ "$CLI_TARGET" == "all" ]]; then
  for candidate in gemini claude kiro codex; do
    if is_cli_available "$candidate"; then
      TARGETS+=("$candidate")
    else
      if [[ "$STRICT_CLI" -eq 1 ]]; then
        echo "error: missing required CLI binary for target '$candidate'"
        exit 1
      fi
      echo "warning: skipping unavailable CLI '$candidate'"
    fi
  done
else
  if ! is_cli_available "$CLI_TARGET"; then
    if [[ "$STRICT_CLI" -eq 1 ]]; then
      echo "error: missing required CLI binary for target '$CLI_TARGET'"
      exit 1
    fi
    echo "warning: selected CLI '$CLI_TARGET' is unavailable; skipping"
  else
    TARGETS+=("$CLI_TARGET")
  fi
fi

if [[ ${#TARGETS[@]} -eq 0 ]]; then
  echo "warning: no target CLIs selected"
  echo "SUMMARY copied=0 missing_source=0 skipped_cli=1"
  exit 0
fi

COPIED=0
MISSING_SOURCE=0
SKIPPED_CLI=0

copy_file() {
  local src="$1"
  local dst="$2"

  if [[ ! -f "$src" ]]; then
    echo "error: missing source file: $src"
    MISSING_SOURCE=$((MISSING_SOURCE + 1))
    return 1
  fi

  if [[ -d "$dst" && ! -L "$dst" ]]; then
    echo "error: destination exists as directory: $dst"
    return 1
  fi

  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "DRY-RUN COPY $src -> $dst"
    return 0
  fi

  mkdir -p "$(dirname "$dst")"
  if cp -f "$src" "$dst" 2>/dev/null; then
    echo "COPIED $src -> $dst"
    COPIED=$((COPIED + 1))
  else
    # Non-fatal no-op when source and destination refer to the same file.
    echo "COPIED $src -> $dst (unchanged)"
  fi
  return 0
}

deploy_gemini() {
  local slug="$1"
  copy_file "$REPO_ROOT/.gemini/skills/$slug/SKILL.md" "$HOME/.gemini/skills/$slug/SKILL.md" || return 1
  copy_file "$REPO_ROOT/.gemini/agents/$slug.md" "$HOME/.gemini/agents/$slug.md" || return 1
  copy_file "$REPO_ROOT/.gemini/commands/$slug.toml" "$HOME/.gemini/commands/$slug.toml" || return 1
}

deploy_claude() {
  local slug="$1"
  copy_file "$REPO_ROOT/.claude/agents/$slug.md" "$HOME/.claude/agents/$slug.md" || return 1
  copy_file "$REPO_ROOT/.claude/commands/$slug.md" "$HOME/.claude/commands/$slug.md" || return 1
}

deploy_kiro() {
  local slug="$1"
  copy_file "$REPO_ROOT/.kiro/skills/$slug/SKILL.md" "$HOME/.kiro/skills/$slug/SKILL.md" || return 1
  copy_file "$REPO_ROOT/.kiro/agents/$slug.json" "$HOME/.kiro/agents/$slug.json" || return 1
  copy_file "$REPO_ROOT/.kiro/prompts/$slug.md" "$HOME/.kiro/prompts/$slug.md" || return 1
}

deploy_codex() {
  local slug="$1"
  copy_file "$REPO_ROOT/.codex/skills/$slug/SKILL.md" "$HOME/.codex/skills/$slug/SKILL.md" || return 1
}

echo "Deploying managed slugs (${#SLUGS[@]}): ${SLUGS[*]}"
echo "Target CLIs: ${TARGETS[*]}"
if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry-run: enabled"
fi

for cli in "${TARGETS[@]}"; do
  if ! is_cli_available "$cli"; then
    SKIPPED_CLI=$((SKIPPED_CLI + 1))
    echo "warning: skipping unavailable CLI '$cli'"
    continue
  fi

  for slug in "${SLUGS[@]}"; do
    case "$cli" in
      gemini) deploy_gemini "$slug" || exit 1 ;;
      claude) deploy_claude "$slug" || exit 1 ;;
      kiro) deploy_kiro "$slug" || exit 1 ;;
      codex) deploy_codex "$slug" || exit 1 ;;
      *)
        echo "error: unsupported CLI target '$cli'"
        exit 1
        ;;
    esac
  done
done

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "SUMMARY copied=0 missing_source=$MISSING_SOURCE skipped_cli=$SKIPPED_CLI"
else
  echo "SUMMARY copied=$COPIED missing_source=$MISSING_SOURCE skipped_cli=$SKIPPED_CLI"
fi

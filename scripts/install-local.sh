#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/install-local.sh [--mode link|copy] [--dry-run]

Installs SSOT-managed generated surfaces into global CLI directories.
Only managed slugs from .meta/manifest.json are touched.

Options:
  --mode link|copy   Install mode (default: link)
  --dry-run          Print planned operations without mutating files
  -h, --help         Show this help
EOF
}

MODE="link"
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      shift
      MODE="${1:-}"
      if [[ "$MODE" != "link" && "$MODE" != "copy" ]]; then
        echo "error: --mode must be 'link' or 'copy'"
        exit 1
      fi
      ;;
    --dry-run)
      DRY_RUN=1
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

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [[ ! -f .meta/manifest.json ]]; then
  echo "error: missing .meta/manifest.json"
  echo "Run build first: python3 scripts/build-surfaces.py"
  exit 1
fi

mapfile -t SLUGS < <(python3 - <<'PY'
import json
from pathlib import Path

manifest = json.loads(Path(".meta/manifest.json").read_text(encoding="utf-8"))
for entry in manifest.get("ssot_sources", []):
    slug = entry.get("slug")
    if slug:
        print(slug)
PY
)

if [[ ${#SLUGS[@]} -eq 0 ]]; then
  echo "error: no managed slugs found in .meta/manifest.json"
  exit 1
fi

echo "Installing managed slugs (${#SLUGS[@]}): ${SLUGS[*]}"
echo "Mode: $MODE"
if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry-run: enabled"
fi

copy_file() {
  local src="$1"
  local dst="$2"
  if [[ ! -f "$src" ]]; then
    echo "error: missing source file: $src"
    exit 1
  fi
  if [[ -d "$dst" && ! -L "$dst" ]]; then
    echo "error: target exists as directory, refusing to overwrite: $dst"
    exit 1
  fi
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "DRY-RUN copy $src -> $dst"
    return
  fi
  mkdir -p "$(dirname "$dst")"
  cp -f "$src" "$dst"
  echo "copied $dst"
}

link_file() {
  local src="$1"
  local dst="$2"
  local src_abs
  if [[ ! -f "$src" ]]; then
    echo "error: missing source file: $src"
    exit 1
  fi
  if [[ -d "$dst" && ! -L "$dst" ]]; then
    echo "error: target exists as directory, refusing to overwrite: $dst"
    exit 1
  fi

  src_abs="$(cd "$(dirname "$src")" && pwd)/$(basename "$src")"
  if [[ -L "$dst" ]]; then
    local current
    current="$(readlink "$dst")"
    if [[ "$current" == "$src_abs" ]]; then
      echo "linked $dst (unchanged)"
      return
    fi
  fi

  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "DRY-RUN link $src_abs -> $dst"
    return
  fi

  mkdir -p "$(dirname "$dst")"
  rm -f "$dst"
  ln -s "$src_abs" "$dst"
  echo "linked $dst"
}

install_file() {
  local src="$1"
  local dst="$2"
  if [[ "$MODE" == "copy" ]]; then
    copy_file "$src" "$dst"
  else
    link_file "$src" "$dst"
  fi
}

for slug in "${SLUGS[@]}"; do
  install_file "$REPO_ROOT/.gemini/skills/$slug/SKILL.md" "$HOME/.gemini/skills/$slug/SKILL.md"
  install_file "$REPO_ROOT/.gemini/agents/$slug.md" "$HOME/.gemini/agents/$slug.md"
  install_file "$REPO_ROOT/.gemini/commands/$slug.toml" "$HOME/.gemini/commands/$slug.toml"

  install_file "$REPO_ROOT/.claude/agents/$slug.md" "$HOME/.claude/agents/$slug.md"
  install_file "$REPO_ROOT/.claude/commands/$slug.md" "$HOME/.claude/commands/$slug.md"

  install_file "$REPO_ROOT/.kiro/skills/$slug/SKILL.md" "$HOME/.kiro/skills/$slug/SKILL.md"
  install_file "$REPO_ROOT/.kiro/agents/$slug.json" "$HOME/.kiro/agents/$slug.json"
  install_file "$REPO_ROOT/.kiro/prompts/$slug.md" "$HOME/.kiro/prompts/$slug.md"

  install_file "$REPO_ROOT/.codex/skills/$slug/SKILL.md" "$HOME/.codex/skills/$slug/SKILL.md"
done

echo "Install complete."

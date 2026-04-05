#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/deploy-surfaces.sh [--cli gemini|claude|kiro|codex|all] [--slug SLUG] [--target PATH] [--allow-nonlocal-target] [--dry-run] [--strict-cli]

Copy-only deployment of SSOT-managed generated surfaces to CLI directories under a target root.
This script never creates symlinks.
If destination file is a symlink, it is unlinked and replaced with a regular file copy.
Existing files are overwritten in place with cp -f.

Options:
  --cli gemini|claude|kiro|codex|all  Target CLI(s). Default: all
  --slug SLUG                         Limit deployment to one slug (repeatable)
  --target PATH                       Destination root path. Default: repository root
  --allow-nonlocal-target             Allow explicit --target outside repository root
  --dry-run                           Show copy actions without writing
  --strict-cli                        Fail when selected CLI binary is not installed
  -h, --help                          Show this help
EOF
}

CLI_TARGET="all"
SLUG_FILTERS=()
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_ROOT="$REPO_ROOT"
DRY_RUN=0
STRICT_CLI=0
ALLOW_NONLOCAL_TARGET=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --cli)
      shift
      CLI_TARGET="${1:-}"
      ;;
    --target)
      shift
      TARGET_ROOT="${1:-}"
      ;;
    --slug)
      shift
      SLUG_FILTERS+=("${1:-}")
      ;;
    --allow-nonlocal-target)
      ALLOW_NONLOCAL_TARGET=1
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

if [[ -z "$TARGET_ROOT" ]]; then
  echo "error: --target requires a non-empty path"
  usage
  exit 1
fi

TARGET_ROOT="$(python3 - "$TARGET_ROOT" <<'PY'
import os
import sys
print(os.path.abspath(os.path.expanduser(sys.argv[1])))
PY
)"

if [[ "$ALLOW_NONLOCAL_TARGET" -ne 1 && "$TARGET_ROOT" != "$REPO_ROOT" && "$TARGET_ROOT" != "$REPO_ROOT"/* ]]; then
  echo "error: --target is restricted to repository root by default: $REPO_ROOT"
  echo "Use --allow-nonlocal-target to write outside repository root"
  exit 1
fi

case "$CLI_TARGET" in
  gemini|claude|kiro|codex|all) ;;
  *)
    echo "error: invalid --cli value: $CLI_TARGET"
    usage
    exit 1
    ;;
esac

cd "$REPO_ROOT"

if [[ ! -f ".meta/manifest.json" ]]; then
  echo "error: missing .meta/manifest.json"
  echo "Run build first: python3 scripts/build-surfaces.py"
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

echo "Target CLIs: ${TARGETS[*]}"

COPIED=0
MISSING_SOURCE=0
REPLACED_SYMLINK=0

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
    if [[ -L "$dst" ]]; then
      echo "DRY-RUN REPLACE-SYMLINK $dst"
    fi
    echo "DRY-RUN COPY $src -> $dst"
    return 0
  fi

  mkdir -p "$(dirname "$dst")"
  if [[ -L "$dst" ]]; then
    rm -f "$dst"
    REPLACED_SYMLINK=$((REPLACED_SYMLINK + 1))
    echo "REPLACED SYMLINK $dst"
  fi
  if cp -f "$src" "$dst" 2>/dev/null; then
    echo "COPIED $src -> $dst"
    COPIED=$((COPIED + 1))
  else
    echo "COPIED $src -> $dst (unchanged)"
  fi
  return 0
}

read_codex_agents() {
  python3 - -- "${SLUG_FILTERS[@]-}" <<'PY'
import json
import sys
from pathlib import Path

separator = sys.argv.index('--')
slug_filters = set(arg for arg in sys.argv[separator + 1:] if arg)
manifest = json.loads(Path('.meta/manifest.json').read_text(encoding='utf-8'))
for entry in manifest.get('ssot_sources', []):
    if slug_filters and entry.get('slug') not in slug_filters:
        continue
    if 'codex_agent' in set(entry.get('expected_surface_names', [])):
        print(entry['slug'])
PY
}

COPY_PLAN_FILE="$(mktemp "${TMPDIR:-/tmp}/core-prompts-deploy-plan.XXXXXX")"
trap 'rm -f "$COPY_PLAN_FILE"' EXIT

python3 scripts/deploy-copy-plan.py "$REPO_ROOT" "$TARGET_ROOT" "${TARGETS[@]}" -- "${SLUG_FILTERS[@]-}" > "$COPY_PLAN_FILE"
if [[ ! -s "$COPY_PLAN_FILE" ]]; then
  echo "warning: nothing to deploy for selected CLI targets"
  echo "SUMMARY copied=0 missing_source=0 skipped_cli=0 replaced_symlink=0"
  exit 0
fi

SLUGS="$(python3 - -- "${SLUG_FILTERS[@]-}" <<'PY'
import json
import sys
from pathlib import Path

separator = sys.argv.index('--')
slug_filters = set(arg for arg in sys.argv[separator + 1:] if arg)
manifest = json.loads(Path('.meta/manifest.json').read_text(encoding='utf-8'))
print(
    ' '.join(
        sorted(
            entry['slug']
            for entry in manifest.get('ssot_sources', [])
            if entry.get('slug') and (not slug_filters or entry['slug'] in slug_filters)
        )
    )
)
PY
)"
echo "Deploying managed slugs: $SLUGS"

while IFS=$'\t' read -r src dst surface slug; do
  [[ -n "$src" ]] || continue
  copy_file "$src" "$dst"
done < "$COPY_PLAN_FILE"

register_codex_agents() {
  local agent_lines="$1"
  local -a agent_args=()
  [[ -n "$agent_lines" ]] || return 0
  local config_path="$TARGET_ROOT/.codex/config.toml"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "DRY-RUN REGISTER codex agents in $config_path: $agent_lines"
    return 0
  fi
  mkdir -p "$(dirname "$config_path")"
  while IFS= read -r agent_slug; do
    [[ -n "$agent_slug" ]] || continue
    agent_args+=("$agent_slug")
  done <<< "$agent_lines"
  python3 scripts/register-codex-agents.py "$config_path" "$TARGET_ROOT" "${agent_args[@]}"
  echo "REGISTERED codex agents in $config_path"
}

if [[ " ${TARGETS[*]} " == *" codex "* ]]; then
  AGENT_LINES="$(read_codex_agents)"
  register_codex_agents "$AGENT_LINES"
fi

echo "SUMMARY copied=$COPIED missing_source=$MISSING_SOURCE skipped_cli=0 replaced_symlink=$REPLACED_SYMLINK"
[[ "$MISSING_SOURCE" -eq 0 ]]

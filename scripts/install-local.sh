#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/install-local.sh [--cli gemini|claude|kiro|codex|all] [--target PATH] [--dry-run] [--strict-cli] [--mode copy]

Legacy compatibility wrapper around deploy-surfaces.sh.
Copy-only behavior is enforced. Symlink mode is removed.

Options:
  --cli gemini|claude|kiro|codex|all  Target CLI(s). Default: all
  --target PATH                       Destination root path. Default: ~
  --dry-run                           Show copy actions without writing
  --strict-cli                        Fail when selected CLI binary is not installed
  --mode copy                         Accepted for backward compatibility only
  -h, --help                          Show this help
EOF
}

ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      shift
      mode="${1:-}"
      if [[ "$mode" != "copy" ]]; then
        echo "error: install-local.sh no longer supports link mode."
        echo "Use copy-only deployment via scripts/deploy-surfaces.sh."
        exit 1
      fi
      ;;
    --cli|--target)
      flag="$1"
      shift
      value="${1:-}"
      if [[ -z "$value" ]]; then
        echo "error: $flag requires a value"
        usage
        exit 1
      fi
      ARGS+=("$flag" "$value")
      ;;
    --dry-run|--strict-cli)
      ARGS+=("$1")
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$SCRIPT_DIR/deploy-surfaces.sh" "${ARGS[@]}"

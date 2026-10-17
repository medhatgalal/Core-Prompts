#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/install-local.sh [--cli agy|gemini|claude|kiro|codex|grok|all] [--target PATH] [--allow-nonlocal-target] [--dry-run] [--strict-cli] [--mode copy]

Compatibility wrapper around deploy-surfaces.sh and its transactional installer.
Unknown, symlinked, and unrecognized partial packages remain preserved, as do
customized skills and custom non-Core agents. Local modifications alone do not
prevent retirement of an exactly identified retired Core-Prompts agent.
Symlink, ambiguous-identity, configuration, and dependency protections still apply.
Removals use a recoverable transaction; review the plan before applying. See
docs/INSTALL-PROFILES.md ("Historical recognition and preservation").
Link installation is unsupported.
When --target points outside this repository, install also writes the standalone updater bundle,
installed VERSION, RELEASE_SOURCE.env, and update_core_prompts.sh
for later release checks.

Options:
  --selection-policy full-catalog|curated  Explicit future skills; one --cli or exact --profile
  --slug SLUG                        Exact skill name (repeatable)
  --profile PATH                     Use a receipt-protected skills profile
  --apply-plan PATH                  Apply a reviewed JSON plan
  --rollback ID                      Restore an installation transaction
  --recover-missing                  Preview exact absent owned Grok skills; --cli grok, --slug and --dry-run required
  --repair                           Recognize historical/current installed skills and agents
  --with-agents                      Explicitly install current skills and agents
  --cli agy|gemini|claude|kiro|codex|grok|all  Target CLI(s). Default: all
  --target PATH                       Destination root path. Default: repository root
  --allow-nonlocal-target             Allow explicit --target outside repository root
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
    --cli|--target|--profile|--apply-plan|--rollback|--slug|--selection-policy)
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
    --allow-nonlocal-target|--dry-run|--strict-cli|--recover-missing|--repair|--with-agents|--surface-only|--list-transactions)
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

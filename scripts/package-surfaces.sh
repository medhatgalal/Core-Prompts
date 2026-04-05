#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/package-surfaces.sh --version vX.Y.Z [--output-dir dist]

Create release artifacts for generated CLI surfaces.

Options:
  --version V      Required release version label (for example: v0.2.1)
  --output-dir DIR Output directory (default: dist)
  -h, --help       Show this help
USAGE
}

VERSION=""
OUTPUT_DIR="dist"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version)
      shift
      VERSION="${1:-}"
      ;;
    --output-dir)
      shift
      OUTPUT_DIR="${1:-}"
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

if [[ -z "$VERSION" ]]; then
  echo "error: --version is required"
  usage
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [[ ! -f ".meta/manifest.json" ]]; then
  echo "error: missing .meta/manifest.json"
  echo "Run build first: python3 scripts/build-surfaces.py"
  exit 1
fi

INCLUDE_PATHS=(
  ".codex"
  ".gemini"
  ".claude"
  ".kiro"
  ".meta/manifest.json"
  ".meta/capability-handoff.json"
  ".meta/capabilities"
  "dist/consumer-shell"
  "sources/ssot-baselines"
  "scripts/deploy-copy-plan.py"
  "scripts/deploy-surfaces.sh"
  "scripts/install-local.sh"
  "docs/CAPABILITY-CATALOG.md"
  "docs/CLI-REFERENCE.md"
  "docs/CAPABILITY-FABRIC.md"
  "docs/UAC-USAGE.md"
  "docs/UAC-CAPABILITY-MODEL.md"
  "docs/GETTING-STARTED.md"
  "docs/EXAMPLES.md"
  "docs/FAQ.md"
  "docs/README.md"
  "docs/ORCHESTRATOR-CONTRACT.md"
  "docs/RELEASE-PACKAGING.md"
  "docs/RELEASE-DELTA.md"
  "docs/STATUS.md"
  "README.md"
  "CONTRIBUTING.md"
  "CHANGELOG.md"
)

for p in "${INCLUDE_PATHS[@]}"; do
  if [[ ! -e "$p" ]]; then
    echo "error: required package path is missing: $p"
    exit 1
  fi
done

mkdir -p "$OUTPUT_DIR"

BASE_NAME="core-prompts-${VERSION}-surfaces"
TAR_PATH="$OUTPUT_DIR/${BASE_NAME}.tar.gz"
ZIP_PATH="$OUTPUT_DIR/${BASE_NAME}.zip"

COPYFILE_DISABLE=1 tar --exclude='.DS_Store' -czf "$TAR_PATH" "${INCLUDE_PATHS[@]}"
zip -rq "$ZIP_PATH" "${INCLUDE_PATHS[@]}" -x '*/.DS_Store' '*.DS_Store'

echo "PACKAGED $TAR_PATH"
echo "PACKAGED $ZIP_PATH"

#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [[ -d .git && -f .meta/manifest.json ]]; then
  echo "manifest exists: .meta/manifest.json"
else
  echo "Run build first: python3 scripts/build-surfaces.py"
  exit 1
fi

if command -v codex >/dev/null 2>&1; then
  echo "Codex CLI detected; syncing skills from local repo path"
else
  echo "Codex CLI not found; skip install"
fi

if command -v gemini >/dev/null 2>&1; then
  echo "Gemini CLI detected; syncing from .gemini"
else
  echo "Gemini CLI not found; skip install"
fi

if command -v claude >/dev/null 2>&1; then
  echo "Claude CLI detected; syncing from .claude"
else
  echo "Claude CLI not found; skip install"
fi

if command -v kiro >/dev/null 2>&1; then
  echo "Kiro CLI detected; syncing from .kiro"
else
  echo "Kiro CLI not found; skip install"
fi

echo "Local files are source-of-truth in repo root for testing and installation workflows."

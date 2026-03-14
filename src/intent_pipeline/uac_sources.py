"""UAC source enumeration for local directories and GitHub tree URLs."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Iterable
from urllib.parse import parse_qs, quote, urlsplit
from urllib.request import Request, urlopen

_ALLOWED_SUFFIXES = {".md", ".txt", ".toml", ".json", ".yaml", ".yml"}
_SKIP_DIR_NAMES = {
    ".git",
    ".github",
    ".claude",
    ".codex",
    ".gemini",
    ".kiro",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".venv",
    "venv",
}
_GITHUB_TREE_RE = re.compile(
    r"^/(?P<owner>[^/]+)/(?P<repo>[^/]+)/(?:tree|blob)/(?P<ref>[^/]+)(?:/(?P<path>.*))?$"
)
_GITHUB_REPO_RE = re.compile(r"^/(?P<owner>[^/]+)/(?P<repo>[^/]+)/?$")


@dataclass(frozen=True, slots=True)
class UacSourceCandidate:
    source_type: str
    display_name: str
    normalized_source: str
    locator: str


@dataclass(frozen=True, slots=True)
class GithubTreeRef:
    owner: str
    repo: str
    ref: str
    path: str
    normalized_source: str


@dataclass(frozen=True, slots=True)
class UacCollectionRecommendation:
    collection_type: str
    recommended_surface: str
    recommended_slug: str
    shared_roof: bool
    rationale: str
    next_actions: tuple[str, ...]

    def as_payload(self) -> dict[str, object]:
        return {
            "collection_type": self.collection_type,
            "recommended_surface": self.recommended_surface,
            "recommended_slug": self.recommended_slug,
            "shared_roof": self.shared_roof,
            "rationale": self.rationale,
            "next_actions": list(self.next_actions),
        }


def enumerate_local_directory(path: Path, *, recurse: bool = True, max_items: int = 50) -> list[UacSourceCandidate]:
    root = path.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Expected directory path, got: {root}")

    candidates: list[UacSourceCandidate] = []
    iterator: Iterable[Path] = root.rglob("*") if recurse else root.iterdir()
    for candidate in sorted(iterator):
        if len(candidates) >= max_items:
            break
        if candidate.is_dir():
            continue
        if any(part in _SKIP_DIR_NAMES for part in candidate.relative_to(root).parts[:-1]):
            continue
        if candidate.suffix.casefold() not in _ALLOWED_SUFFIXES and candidate.name != "SKILL.md":
            continue
        candidates.append(
            UacSourceCandidate(
                source_type="LOCAL_FILE",
                display_name=str(candidate.relative_to(root)),
                normalized_source=str(candidate),
                locator=str(candidate),
            )
        )
    return candidates


def parse_github_tree_url(url: str) -> GithubTreeRef | None:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != "github.com":
        return None
    match = _GITHUB_TREE_RE.match(parsed.path)
    if match:
        path = (match.group("path") or "").strip("/")
        normalized_path = f"/{path}" if path else ""
        return GithubTreeRef(
            owner=match.group("owner"),
            repo=match.group("repo"),
            ref=match.group("ref"),
            path=path,
            normalized_source=f"https://github.com/{match.group('owner')}/{match.group('repo')}/tree/{match.group('ref')}{normalized_path}",
        )
    repo_match = _GITHUB_REPO_RE.match(parsed.path)
    if repo_match:
        ref = _resolve_github_default_branch(repo_match.group("owner"), repo_match.group("repo"))
        return GithubTreeRef(
            owner=repo_match.group("owner"),
            repo=repo_match.group("repo"),
            ref=ref,
            path="",
            normalized_source=f"https://github.com/{repo_match.group('owner')}/{repo_match.group('repo')}/tree/{ref}",
        )
    return None


def enumerate_github_tree(
    url: str,
    *,
    recurse: bool = True,
    max_items: int = 50,
    timeout_seconds: int = 15,
) -> tuple[GithubTreeRef, list[UacSourceCandidate]]:
    tree_ref = parse_github_tree_url(url)
    if tree_ref is None:
        raise ValueError(f"Unsupported GitHub source: {url}")

    queue = [tree_ref.path]
    candidates: list[UacSourceCandidate] = []
    seen_paths: set[str] = set()
    while queue and len(candidates) < max_items:
        current_path = queue.pop(0)
        if current_path in seen_paths:
            continue
        seen_paths.add(current_path)
        payload = _github_contents(tree_ref.owner, tree_ref.repo, tree_ref.ref, current_path, timeout_seconds)
        if isinstance(payload, dict):
            payload = [payload]
        for entry in payload:
            entry_type = str(entry.get("type", ""))
            entry_path = str(entry.get("path", "")).strip()
            if not entry_path:
                continue
            if entry_type == "dir":
                if recurse:
                    queue.append(entry_path)
                continue
            if entry_type != "file":
                continue
            candidate_path = Path(entry_path)
            if candidate_path.suffix.casefold() not in _ALLOWED_SUFFIXES and candidate_path.name != "SKILL.md":
                continue
            download_url = entry.get("download_url")
            html_url = entry.get("html_url") or entry_path
            if not isinstance(download_url, str) or not download_url:
                continue
            candidates.append(
                UacSourceCandidate(
                    source_type="URL",
                    display_name=entry_path,
                    normalized_source=str(html_url),
                    locator=download_url,
                )
            )
            if len(candidates) >= max_items:
                break
    return tree_ref, candidates


def aggregate_collection_recommendation(
    source_label: str,
    item_payloads: list[dict[str, object]],
) -> UacCollectionRecommendation:
    accepted = [item for item in item_payloads if item.get("status") == "accepted"]
    if not accepted:
        return UacCollectionRecommendation(
            collection_type="manual_review",
            recommended_surface="manual_review",
            recommended_slug=_slugify(source_label),
            shared_roof=False,
            rationale="No items passed deterministic UAC intake. Review the source set manually.",
            next_actions=(
                "Inspect individual items and add explicit objective/scope markers.",
                "Exclude config-only or unsuitable files before packaging.",
            ),
        )

    surface_counts: dict[str, int] = {}
    for item in accepted:
        surface = str(item.get("uac", {}).get("recommended_surface", "manual_review"))
        surface_counts[surface] = surface_counts.get(surface, 0) + 1
    dominant_surface = max(surface_counts, key=surface_counts.get)
    shared_roof = len(accepted) > 1 and surface_counts[dominant_surface] == len(accepted)

    if dominant_surface == "skill" and len(accepted) >= 2:
        return UacCollectionRecommendation(
            collection_type="skill_family",
            recommended_surface="skill",
            recommended_slug=_slugify(source_label),
            shared_roof=shared_roof,
            rationale=(
                f"{len(accepted)} accepted items read like reusable prompt/skill assets. Package them under one "
                f"{_slugify(source_label)} skill family with named modes or subcommands."
            ),
            next_actions=(
                "Group the prompts under one family-level entry surface.",
                "Preserve per-file specializations as named modes.",
                "Normalize shared constraints and output conventions once at the family level.",
            ),
        )
    if dominant_surface == "agent" and len(accepted) >= 2:
        return UacCollectionRecommendation(
            collection_type="agent_family",
            recommended_surface="agent",
            recommended_slug=_slugify(source_label),
            shared_roof=shared_roof,
            rationale=(
                f"{len(accepted)} accepted items expose agent-like control-plane behavior. Keep them under one "
                f"{_slugify(source_label)} agent family rather than collapsing them into a single skill."
            ),
            next_actions=(
                "Preserve agent boundaries and explicit tool declarations.",
                "Split reusable guidance from agent-only orchestration metadata.",
                "Review any mixed prompt/config items manually before emitting agents.",
            ),
        )
    return UacCollectionRecommendation(
        collection_type="mixed_review",
        recommended_surface="manual_review",
        recommended_slug=_slugify(source_label),
        shared_roof=False,
        rationale=(
            "The source set mixes different shapes or confidence levels. Review the accepted items manually before "
            "deciding whether to ship one family or several separate surfaces."
        ),
        next_actions=(
            "Split agent-like and skill-like items into separate groups.",
            "Remove config-only items from the packaging set.",
            "Re-run UAC after narrowing the collection to one coherent family.",
        ),
    )


def _github_contents(owner: str, repo: str, ref: str, path: str, timeout_seconds: int) -> object:
    encoded_path = quote(path)
    endpoint = f"https://api.github.com/repos/{owner}/{repo}/contents/{encoded_path}" if path else f"https://api.github.com/repos/{owner}/{repo}/contents"
    query = parse_qs("")
    query_string = f"?ref={quote(ref)}"
    request = Request(
        endpoint + query_string,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "core-prompts-uac-import",
        },
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def _resolve_github_default_branch(owner: str, repo: str) -> str:
    endpoint = f"https://api.github.com/repos/{owner}/{repo}"
    request = Request(
        endpoint,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "core-prompts-uac-import",
        },
    )
    with urlopen(request, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))
    default_branch = payload.get("default_branch")
    if not isinstance(default_branch, str) or not default_branch.strip():
        raise ValueError(f"Could not resolve default branch for {owner}/{repo}")
    return default_branch.strip()


def _slugify(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return text or "uac-import"


__all__ = [
    "GithubTreeRef",
    "UacCollectionRecommendation",
    "UacSourceCandidate",
    "aggregate_collection_recommendation",
    "enumerate_github_tree",
    "enumerate_local_directory",
    "parse_github_tree_url",
]

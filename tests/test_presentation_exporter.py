"""Execute the complete Swift exporter with deterministic test-only phase hooks.

Requires macOS 13+, Swift, a macOS SDK and a working local AppKit/WebKit session.
Other platforms or missing toolchains skip explicitly. Compilation is bounded at
120 seconds; each exporter has a 20-second internal and 35-second outer timeout.
The helper is compiled once per module, using an isolated temporary module cache.
No dependencies are installed, and the synthetic HTML has no network resources.
These tests cover particular writer orderings, not atomic concurrency safety.
"""
from __future__ import annotations

import hashlib
import os
import platform
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
EXPORTER = (
    ROOT / "sources" / "capability-resources"
    / "engos-content-dynamic-html-presentations" / "export_slides.swift"
)
pytestmark = pytest.mark.skipif(
    sys.platform != "darwin", reason="Swift PNG exporter requires macOS AppKit/WebKit"
)

HOOK_ENV = "CORE_PROMPTS_EXPORTER_TEST_PHASE"
ARRIVING = b"INDEPENDENT_ARRIVING_PNG"
REPLACEMENT = b"INDEPENDENT_USER_REPLACEMENT"
EXTRA = b"INDEPENDENT_EXTRA_FILE"
ORIGINALS = {
    f"slide-{number:02}.png": f"ORIGINAL_{number}".encode()
    for number in range(1, 4)
}
HTML = """<!doctype html><html><head><meta charset="utf-8"><style>
html,body{margin:0;width:100%;height:100%}.slide{display:none;padding:20px;
box-sizing:border-box;width:100vw;height:100vh;font:24px system-ui}
.slide.active{display:block}#one{background:#dbeafe}#two{background:#dcfce7}
#three{background:#fef3c7}
</style></head><body><section id="one" class="slide active">First public slide</section>
<section id="two" class="slide">Second public slide</section>
<section id="three" class="slide">Third public slide</section></body></html>"""


def _insert_once(source: str, anchor: str, replacement: str) -> str:
    if source.count(anchor) != 1:
        pytest.fail(f"Exporter phase hook no longer has one insertion point: {anchor!r}")
    return source.replace(anchor, replacement, 1)


def _instrument(source: str) -> str:
    # These checks bind hooks to phases; behavioral assertions run the binary.
    source = _insert_once(
        source,
        "    try retainedExporter?.start()\n",
        """    try retainedExporter?.start()
    if ProcessInfo.processInfo.environment["CORE_PROMPTS_EXPORTER_TEST_PHASE"] == "after_prepare" {
        try Data("INDEPENDENT_ARRIVING_PNG".utf8).write(
            to: options.output.appendingPathComponent("slide-02.png"),
            options: .withoutOverwriting
        )
        print("TEST_INJECTED_AFTER_PREPARE"); fflush(stdout)
    }
""",
    )
    source = _insert_once(
        source,
        "            let finalNames = Set(",
        """            if ProcessInfo.processInfo.environment["CORE_PROMPTS_EXPORTER_TEST_PHASE"] == "after_promotion" {
                try Data("INDEPENDENT_USER_REPLACEMENT".utf8).write(
                    to: options.output.appendingPathComponent("slide-01.png"), options: .atomic
                )
                try Data("INDEPENDENT_EXTRA_FILE".utf8).write(
                    to: options.output.appendingPathComponent("slide-99.png"), options: .withoutOverwriting
                )
                print("TEST_INJECTED_REPLACEMENT_AFTER_PROMOTION"); fflush(stdout)
            }
            let finalNames = Set(""",
    )
    return _insert_once(
        source,
        "            for (staged, final) in zip(stagedFiles, expectedFiles) {\n",
        """            for (staged, final) in zip(stagedFiles, expectedFiles) {
                if ProcessInfo.processInfo.environment["CORE_PROMPTS_EXPORTER_TEST_PHASE"] == "forced_rollback"
                    && final.lastPathComponent == "slide-03.png" {
                    try manager.removeItem(at: staged)
                    print("TEST_INJECTED_MISSING_THIRD_STAGE"); fflush(stdout)
                }
""",
    )


@pytest.fixture(scope="module")
def exporter_binary(tmp_path_factory: pytest.TempPathFactory) -> Path:
    version = platform.mac_ver()[0]
    if version and int(version.split(".", 1)[0]) < 13:
        pytest.skip("Swift PNG exporter requires macOS 13 or later")
    compiler, xcrun = shutil.which("swiftc"), shutil.which("xcrun")
    if compiler is None or xcrun is None:
        pytest.skip("Swift compiler and xcrun are required for native exporter regressions")
    sdk = subprocess.run(
        [xcrun, "--sdk", "macosx", "--show-sdk-path"],
        capture_output=True, text=True, timeout=10, check=False,
    )
    if sdk.returncode != 0:
        pytest.skip(f"macOS SDK unavailable: {sdk.stderr.strip()[:300]}")
    work = tmp_path_factory.mktemp("presentation-exporter-build")
    source = work / "exporter.swift"
    source.write_text(_instrument(EXPORTER.read_text(encoding="utf-8")), encoding="utf-8")
    cache = work / "module-cache"
    cache.mkdir()
    executable = work / "exporter"
    result = subprocess.run(
        [compiler, str(source), "-o", str(executable), "-module-cache-path", str(cache)],
        capture_output=True, text=True, timeout=120, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return executable


@pytest.fixture
def workspace(tmp_path: Path) -> tuple[Path, Path]:
    deck = tmp_path / "deck.html"
    deck.write_text(HTML, encoding="utf-8")
    output = tmp_path / "output"
    output.mkdir()
    (output / "keep.bin").write_bytes(b"\x00UNRELATED\xff")
    (output / "nested").mkdir()
    (output / "nested" / "notes.txt").write_text("USER NOTES", encoding="utf-8")
    (output / "slide-review.png").write_bytes(b"NOT_A_NUMERIC_SLIDE")
    return deck, output


def _run(binary: Path, deck: Path, output: Path, *, phase: str = "", force: bool = False):
    env = os.environ.copy()
    env.pop(HOOK_ENV, None)
    if phase:
        env[HOOK_ENV] = phase
    command = [
        str(binary), "--input", str(deck), "--output", str(output),
        "--width", "320", "--height", "180", "--timeout", "20",
    ]
    if force:
        command.append("--force")
    return subprocess.run(
        command, env=env, capture_output=True, text=True, timeout=35, check=False,
    )


def _check_unrelated(output: Path) -> None:
    assert (output / "keep.bin").read_bytes() == b"\x00UNRELATED\xff"
    assert (output / "nested" / "notes.txt").read_text() == "USER NOTES"
    assert (output / "slide-review.png").read_bytes() == b"NOT_A_NUMERIC_SLIDE"


def _check_no_recovery_directories(output: Path) -> None:
    assert not list(output.glob(".slide-backup-*"))
    assert not list(output.glob(".slide-export-*"))


def _seed_originals(output: Path) -> None:
    for name, content in ORIGINALS.items():
        (output / name).write_bytes(content)


def test_no_force_preserves_file_arriving_after_preparation(exporter_binary, workspace):
    deck, output = workspace
    result = _run(exporter_binary, deck, output, phase="after_prepare")
    assert result.returncode != 0, result.stdout + result.stderr
    assert "TEST_INJECTED_AFTER_PREPARE" in result.stdout
    assert result.stdout.index("TEST_INJECTED_AFTER_PREPARE") < result.stdout.index("[1/3]")
    assert "Refusing replacement without --force" in result.stderr
    assert "Exported and verified" not in result.stdout
    assert (output / "slide-02.png").read_bytes() == ARRIVING
    assert not (output / "slide-01.png").exists()
    assert not (output / "slide-03.png").exists()
    _check_unrelated(output)
    _check_no_recovery_directories(output)


def test_rollback_preserves_changed_output_and_recovery_backup(exporter_binary, workspace):
    deck, output = workspace
    _seed_originals(output)
    result = _run(exporter_binary, deck, output, phase="after_promotion", force=True)
    assert result.returncode != 0, result.stdout + result.stderr
    assert "TEST_INJECTED_REPLACEMENT_AFTER_PROMOTION" in result.stdout
    assert result.stdout.index("[3/3]") < result.stdout.index("TEST_INJECTED_REPLACEMENT_AFTER_PROMOTION")
    assert "Exported and verified" not in result.stdout
    assert "Rollback incomplete" in result.stderr
    assert (output / "slide-01.png").read_bytes() == REPLACEMENT
    assert (output / "slide-99.png").read_bytes() == EXTRA
    assert (output / "slide-02.png").read_bytes() == ORIGINALS["slide-02.png"]
    assert (output / "slide-03.png").read_bytes() == ORIGINALS["slide-03.png"]
    backups = list(output.glob(".slide-backup-*"))
    staging = list(output.glob(".slide-export-*"))
    assert len(backups) == len(staging) == 1
    assert (backups[0] / "slide-01.png").read_bytes() == ORIGINALS["slide-01.png"]
    recovery = re.search(r"Recovery backup: (.+?); staging: (.+?)\. Original error:", result.stderr)
    assert recovery is not None, result.stderr
    assert Path(recovery.group(1)).resolve() == backups[0].resolve()
    assert Path(recovery.group(2)).resolve() == staging[0].resolve()
    _check_unrelated(output)


def test_ordinary_forced_rollback_restores_originals(exporter_binary, workspace):
    deck, output = workspace
    _seed_originals(output)
    result = _run(exporter_binary, deck, output, phase="forced_rollback", force=True)
    assert result.returncode != 0, result.stdout + result.stderr
    assert "TEST_INJECTED_MISSING_THIRD_STAGE" in result.stdout
    assert "Rollback incomplete" not in result.stderr
    assert "Exported and verified" not in result.stdout
    assert {name: (output / name).read_bytes() for name in ORIGINALS} == ORIGINALS
    _check_unrelated(output)
    _check_no_recovery_directories(output)


@pytest.mark.parametrize("force", [False, True], ids=["fresh", "explicit-force"])
def test_successful_exports_preserve_controls(exporter_binary, workspace, force):
    deck, output = workspace
    if force:
        _seed_originals(output)
    result = _run(exporter_binary, deck, output, force=force)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Exported and verified 3 slide(s)" in result.stdout
    images = [(output / name).read_bytes() for name in ORIGINALS]
    assert all(image.startswith(b"\x89PNG\r\n\x1a\n") for image in images)
    assert all(struct.unpack(">II", image[16:24]) == (320, 180) for image in images)
    assert len({hashlib.sha256(image).digest() for image in images}) == 3
    _check_unrelated(output)
    _check_no_recovery_directories(output)


def test_broken_image_fails_without_publication(exporter_binary, workspace):
    deck, output = workspace
    deck.write_text(HTML.replace("</body>", '<img src="images/missing.png" loading="eager"></body>'))
    result = _run(exporter_binary, deck, output)
    assert result.returncode != 0, result.stdout + result.stderr
    assert "Broken image assets: images/missing.png" in result.stderr
    assert "Exported and verified" not in result.stdout
    assert all(not (output / name).exists() for name in ORIGINALS)
    _check_unrelated(output)
    _check_no_recovery_directories(output)

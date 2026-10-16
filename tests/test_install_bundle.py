"""Check committed runtime identity before any generation can repair drift."""
from pathlib import Path

import pytest

from scripts import install_bundle


ROOT = Path(__file__).resolve().parents[1]


def test_checked_in_install_bundle_matches_runtime() -> None:
    install_bundle.verified(ROOT)


@pytest.mark.parametrize("drift", ["content", "mode"])
def test_runtime_drift_is_rejected_without_rewriting(tmp_path: Path, drift: str) -> None:
    for relative in ("VERSION", "scripts/deploy-profile.py",
                     "scripts/update-core-prompts.py", "scripts/install-local.sh"):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture runtime\n")
        path.chmod(0o755)
    (tmp_path / ".meta").mkdir()
    install_bundle.build(tmp_path)
    assert install_bundle.verified(tmp_path)
    wrapper = tmp_path / "scripts/install-local.sh"
    if drift == "content":
        wrapper.write_text(wrapper.read_text() + "# help text changed\n")
    else:
        wrapper.chmod(0o644)
    before = {p.relative_to(tmp_path): (p.read_bytes(), p.stat().st_mode)
              for p in tmp_path.rglob("*") if p.is_file()}

    with pytest.raises(ValueError, match="identity mismatch: scripts/install-local\\.sh"):
        install_bundle.verified(tmp_path)

    after = {p.relative_to(tmp_path): (p.read_bytes(), p.stat().st_mode)
             for p in tmp_path.rglob("*") if p.is_file()}
    assert after == before

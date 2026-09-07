"""Optional export boundaries; no live Google writes in this suite."""
from pathlib import Path
from types import SimpleNamespace
import importlib.util
import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("opex_exports", ROOT / "sources/capability-resources/engos-audit-opex-incident-review/export_report.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@pytest.fixture
def source(tmp_path):
    path = tmp_path / "BRIEFING.html"
    path.write_text('<html><head><style>hidden</style></head><body><nav>duplicate nav</nav><h1>Daily Digest</h1><table><tr><th>Fix</th><th>Why it helps</th></tr><tr><td>FIX-11</td><td>Prevents &lt;failure&gt;</td></tr></table><details><summary>INC-101</summary><h3>What to say</h3><p>The fix is not deployed.</p></details></body></html>')
    return path


def test_plain_export_preserves_table_and_closed_details(source, tmp_path):
    output = tmp_path / "BRIEFING.txt"
    receipt = MODULE.export_report(source, "txt", output=output)
    text = output.read_text()
    assert "Fix | Why it helps" in text
    assert "FIX-11 | Prevents <failure>" in text
    assert "INC-101" in text and "The fix is not deployed." in text
    assert "hidden" not in text and "duplicate nav" not in text
    assert receipt["status"] == "exported"
    with pytest.raises(MODULE.ExportError, match="overwrite"):
        MODULE.export_report(source, "txt", output=output)


def test_google_export_requires_exact_destination_and_explicit_write(source, monkeypatch):
    monkeypatch.setattr(MODULE.subprocess, "run", lambda *a, **k: pytest.fail("unexpected external call"))
    with pytest.raises(MODULE.ExportError, match="document ID"):
        MODULE.export_report(source, "gdoc")
    with pytest.raises(MODULE.ExportError, match="authorize-google-write"):
        MODULE.export_report(source, "gdoc", document="DOC_ID")
    assert MODULE.export_report(source, "gdoc", document="DOC_ID", dry_run=True)["status"] == "planned"


def test_google_failure_never_claims_success_or_retries(source, monkeypatch):
    calls = []
    monkeypatch.setattr(MODULE.shutil, "which", lambda name: f"/fake/{name}")
    def run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=1)
    monkeypatch.setattr(MODULE.subprocess, "run", run)
    with pytest.raises(MODULE.ExportError, match="failed or uncertain"):
        MODULE.export_report(source, "gdoc", document="DOC_ID", authorize_google_write=True)
    assert len(calls) == 1
    assert calls[0][:6] == ["/fake/gws", "docs", "+write", "--document", "DOC_ID", "--text"]


def test_google_ack_requires_separate_readback(source, monkeypatch):
    monkeypatch.setattr(MODULE.shutil, "which", lambda name: f"/fake/{name}")
    monkeypatch.setattr(MODULE.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=0))
    receipt = MODULE.export_report(source, "gdoc", document="DOC_ID", authorize_google_write=True)
    assert receipt["status"] == "write_acknowledged"
    assert "not content verification" in receipt["readback"]


def test_pdf_missing_converter_retains_source(source, tmp_path, monkeypatch):
    original = source.read_bytes()
    monkeypatch.setattr(MODULE.shutil, "which", lambda name: None)
    output = tmp_path / "BRIEFING.pdf"
    with pytest.raises(MODULE.ExportError, match="unavailable"):
        MODULE.export_report(source, "pdf", output=output)
    assert source.read_bytes() == original and not output.exists()


def test_pdf_checks_signature_and_never_overwrites_racing_destination(source, tmp_path, monkeypatch):
    output = tmp_path / "BRIEFING.pdf"
    monkeypatch.setattr(MODULE.shutil, "which", lambda name: f"/fake/{name}")
    def invalid(command, **kwargs):
        Path(command[-1]).write_bytes(b"not PDF")
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(MODULE.subprocess, "run", invalid)
    with pytest.raises(MODULE.ExportError, match="conversion failed"):
        MODULE.export_report(source, "pdf", output=output)
    assert not output.exists()
    def racing(command, **kwargs):
        assert "--sandbox" in command
        assert "-raw_tex-raw_html" in command[2]
        Path(command[-1]).write_bytes(b"%PDF-fixture")
        output.write_text("preserve")
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(MODULE.subprocess, "run", racing)
    with pytest.raises(FileExistsError):
        MODULE.export_report(source, "pdf", output=output)
    assert output.read_text() == "preserve"


def test_plain_export_separates_real_digest_metric_cards():
    import json
    path = ROOT / "sources/capability-resources/engos-audit-opex-incident-review/opex_digest.py"
    spec = importlib.util.spec_from_file_location("digest_export_fixture", path)
    digest = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(digest)
    fixtures = ROOT / "tests/fixtures/opex_digest"
    value = digest.build_model(json.loads((fixtures / "current.json").read_text()), json.loads((fixtures / "previous.json").read_text()))
    text = MODULE.plain_text(digest.render_html(value))
    assert "0 New" in text
    assert "3 Open total" in text
    assert "1 Chronic" in text
    assert "0New3Open" not in text
    assert "Five Whys" in text


def test_google_timeout_is_explicit_and_not_retried(source, monkeypatch):
    monkeypatch.setattr(MODULE.shutil, "which", lambda name: f"/fake/{name}")
    calls = []
    def timeout(command, **kwargs):
        calls.append(command)
        raise MODULE.subprocess.TimeoutExpired(command, kwargs["timeout"])
    monkeypatch.setattr(MODULE.subprocess, "run", timeout)
    with pytest.raises(MODULE.ExportError, match="timed out"):
        MODULE.export_report(source, "gdoc", document="DOC_ID", authorize_google_write=True)
    assert len(calls) == 1

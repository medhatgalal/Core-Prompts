"""Optional exports from an already-rendered local OpEx HTML report.

The digest renderer remains network-free. Only explicitly authorized gdoc export
calls an external provider; missing tools leave the existing report untouched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from html.parser import HTMLParser
from pathlib import Path


class ExportError(ValueError):
    pass


class _PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in {"style", "script", "nav", "head"}:
            self.hidden.append(tag)
        if not self.hidden and tag in {"h1", "h2", "h3", "p", "tr", "li", "dt", "dd", "summary", "footer", "div"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if self.hidden and self.hidden[-1] == tag:
            self.hidden.pop()
        elif not self.hidden and tag in {"strong", "span"}:
            self.parts.append(" ")
        elif not self.hidden and tag in {"td", "th"}:
            self.parts.append(" | ")
        elif not self.hidden and tag in {"h1", "h2", "h3", "p", "tr", "li", "dt", "dd", "summary", "footer", "div"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def plain_text(source: str) -> str:
    parser = _PlainText()
    parser.feed(source)
    return "\n".join(line.strip().removesuffix("|").rstrip() for line in "".join(parser.parts).splitlines() if line.strip()) + "\n"


def _run(command: list[str], **kwargs):
    try:
        return subprocess.run(command, timeout=120, **kwargs)
    except subprocess.TimeoutExpired as exc:
        raise ExportError("export timed out; retain local files and inspect the destination before retrying a Google write") from exc


def export_report(source: Path, output_format: str, *, output: Path | None = None,
                  document: str | None = None, authorize_google_write: bool = False,
                  dry_run: bool = False) -> dict:
    raw = source.read_bytes()
    text = plain_text(raw.decode("utf-8"))
    if not text.strip():
        raise ExportError("source report contains no text")
    if output_format not in {"txt", "pdf", "gdoc"}:
        raise ExportError("format must be txt, pdf or gdoc")
    if output_format == "gdoc":
        if output is not None or not document or not re.fullmatch(r"[A-Za-z0-9_-]+", document):
            raise ExportError("gdoc requires an explicit existing document ID and no local output")
        if not dry_run and not authorize_google_write:
            raise ExportError("gdoc requires explicit --authorize-google-write for the named document")
    elif document is not None or output is None or output.suffix.lower() != f".{output_format}":
        raise ExportError("local export requires a matching output extension and no document ID")
    elif output.exists():
        raise ExportError(f"refusing to overwrite existing export: {output}")
    receipt = {"format": output_format, "source_sha256": hashlib.sha256(raw).hexdigest(),
               "target": str(output) if output is not None else document,
               "status": "planned" if dry_run else "exported"}
    if dry_run:
        return receipt
    if output_format == "txt":
        with output.open("x", encoding="utf-8") as handle:
            handle.write(text)
    elif output_format == "pdf":
        pandoc = shutil.which("pandoc")
        if not pandoc:
            raise ExportError("Pandoc unavailable; retain local HTML/Markdown")
        # Convert escaped plain content, not active HTML/TeX or remote assets.
        safe = re.sub(r"([\\`*_{}\[\]()#+.!|>~-])", r"\\\1", text)
        with tempfile.TemporaryDirectory(prefix=".opex-export-", dir=output.parent) as scratch:
            candidate = Path(scratch) / "report.pdf"
            result = _run([pandoc, "--sandbox", "--from=markdown-raw_tex-raw_html", "--output", str(candidate)], input=safe, text=True, capture_output=True, check=False)
            if result.returncode or not candidate.exists() or not candidate.read_bytes().startswith(b"%PDF-"):
                raise ExportError("PDF conversion failed or PDF engine unavailable; retain local HTML/Markdown")
            # Publish without overwriting a target created after preflight.
            os.link(candidate, output)
    else:
        gws = shutil.which("gws")
        if not gws:
            raise ExportError("GWS unavailable; retain local HTML/Markdown")
        result = _run([gws, "docs", "+write", "--document", document, "--text", text], capture_output=True, text=True, check=False)
        if result.returncode:
            raise ExportError("Google Docs write failed or uncertain; retain local files and inspect the document before any retry")
        receipt["status"] = "write_acknowledged"
        receipt["readback"] = "required; CLI acknowledgement is not content verification"
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--format", required=True, choices=("txt", "pdf", "gdoc"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--document")
    parser.add_argument("--authorize-google-write", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(export_report(args.source, args.format, output=args.output,
                                      document=args.document, authorize_google_write=args.authorize_google_write,
                                      dry_run=args.dry_run), indent=2))
    except (ExportError, OSError, UnicodeError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()

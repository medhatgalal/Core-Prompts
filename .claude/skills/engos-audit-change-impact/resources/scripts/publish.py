#!/usr/bin/env python3
"""Publish a markdown report as a private Google Doc (create, or update in place).

Requires `pandoc` and the `gws` CLI. Exit codes:
  0  published and verified (pageless, table borders, links present)
  2  not published (tools missing, signed out, upload failed, or doc is shared);
     the caller delivers the markdown file instead and says why
  3  published but the format check failed; the caller reports what failed
  1  usage error (for example --title missing when creating)

  publish.py --md report.md --title "Org change rollup: ..."       # create
  publish.py --md report.md --doc-id <id>                          # replace content
Updating refuses a doc that anyone other than its owner can open, unless
--allow-shared is passed (the person must have agreed to republish to readers).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile


def run(args, cwd=None):
    try:
        p = subprocess.run(args, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=300, cwd=cwd)
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    return p.returncode, p.stdout, p.stderr


def gws_json(args, cwd=None):
    code, out, err = run(["gws"] + args, cwd=cwd)
    start = out.find("{")
    try:
        data = json.loads(out[start:]) if start >= 0 else {}
    except ValueError:
        data = {}
    return code, data, err


def fail(code, reason, md):
    print(json.dumps({"published": False, "reason": reason, "markdown": md}))
    sys.exit(code)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", required=True)
    ap.add_argument("--title")
    ap.add_argument("--doc-id")
    ap.add_argument("--allow-shared", action="store_true")
    a = ap.parse_args()
    md = os.path.abspath(a.md)
    if not (shutil.which("pandoc") and shutil.which("gws")):
        fail(2, "pandoc or gws not installed", md)
    if not a.doc_id and not a.title:
        sys.exit("publish: --title is required when creating a new doc")
    if a.doc_id and not a.allow_shared:
        code, perms, err = gws_json(["drive", "permissions", "list", "--params", json.dumps({"fileId": a.doc_id, "fields": "permissions(role,type)"})])
        if code or "permissions" not in perms:
            fail(2, f"could not read sharing for {a.doc_id}: {(perms.get('error') or {}).get('message') or err[:200]}", md)
        others = [p for p in perms["permissions"] if p.get("role") != "owner"]
        if others:
            fail(2, f"doc is shared with {len(others)} other principal(s); re-run with --allow-shared only if the person agreed", md)
    # gws uploads only files under its working directory: build the .docx next to the markdown.
    with tempfile.TemporaryDirectory(dir=os.path.dirname(md)) as tmp:
        code, _, err = run(["pandoc", md, "-o", os.path.join(tmp, "report.docx")])
        if code:
            fail(2, f"pandoc failed: {err[:300]}", md)
        if a.doc_id:
            code, meta, err = gws_json(["drive", "files", "update", "--params", json.dumps({"fileId": a.doc_id, "fields": "id,name"}),
                                        "--upload", "report.docx"] + (["--json", json.dumps({"name": a.title})] if a.title else []), cwd=tmp)
        else:
            code, meta, err = gws_json(["drive", "files", "create", "--json", json.dumps({"name": a.title, "mimeType": "application/vnd.google-apps.document"}),
                                        "--upload", "report.docx", "--params", json.dumps({"fields": "id,name"})], cwd=tmp)
    doc_id = meta.get("id")
    if not doc_id:
        fail(2, f"upload failed: {(meta.get('error') or {}).get('message') or err[:300]}", md)
    _, doc, _ = gws_json(["docs", "documents", "get", "--params", json.dumps({"documentId": doc_id})])
    reqs = [{"updateDocumentStyle": {"documentStyle": {"documentFormat": {"documentMode": "PAGELESS"}}, "fields": "documentFormat"}}]
    border = {"color": {"color": {"rgbColor": {"red": 0.6, "green": 0.6, "blue": 0.6}}}, "width": {"magnitude": 1, "unit": "PT"}, "dashStyle": "SOLID"}
    for e in doc.get("body", {}).get("content", []):
        if "table" in e:
            reqs.append({"updateTableCellStyle": {"tableStartLocation": {"index": e["startIndex"]},
                                                  "tableCellStyle": {"borderTop": border, "borderBottom": border, "borderLeft": border, "borderRight": border},
                                                  "fields": "borderTop,borderBottom,borderLeft,borderRight"}})
    gws_json(["docs", "documents", "batchUpdate", "--params", json.dumps({"documentId": doc_id}), "--json", json.dumps({"requests": reqs})])
    _, doc, _ = gws_json(["docs", "documents", "get", "--params", json.dumps({"documentId": doc_id})])
    body = doc.get("body", {}).get("content", [])
    tables = [e for e in body if "table" in e]
    bordered = all(t["table"]["tableRows"][0]["tableCells"][0].get("tableCellStyle", {}).get("borderTop", {}).get("width") for t in tables)
    links = sum(1 for e in body for el in e.get("paragraph", {}).get("elements", []) if el.get("textRun", {}).get("textStyle", {}).get("link"))
    pageless = doc.get("documentStyle", {}).get("documentFormat", {}).get("documentMode") == "PAGELESS"
    res = {"published": True, "doc_id": doc_id, "url": f"https://docs.google.com/document/d/{doc_id}/edit",
           "pageless": pageless, "tables": len(tables), "tables_bordered": bordered, "links": links}
    print(json.dumps(res))
    sys.exit(0 if pageless and bordered and links else 3)


if __name__ == "__main__":
    main()

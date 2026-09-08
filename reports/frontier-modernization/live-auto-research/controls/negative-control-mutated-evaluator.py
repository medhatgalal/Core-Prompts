import ast
import hashlib
import json
import sys
from pathlib import Path

CASES = [
    ("empty", "", ""),
    ("unchanged", "plain", "plain"),
    ("trim_ascii", "  hello  ", "hello"),
    ("only_whitespace", " \t\n\r\v\f", ""),
    ("repeated_spaces", "a   b", "a b"),
    ("internal_tab", "a\tb", "a b"),
    ("internal_newline", "a\nb", "a b"),
    ("mixed_runs", " \ta \n\tb\r\n c  ", "a b c"),
    ("nonbreaking_space", "café\u00a0\u00a0東京", "café 東京"),
    ("unicode_em_space", "\u2003東京\u2003\u2003مرحبا\u2003", "東京 مرحبا"),
    ("unicode_unchanged", "café 東京 مرحبا", "café 東京 مرحبا"),
    ("emoji", " 🙂\t🚀 ", "🙂 🚀"),
    ("combining_character", "e\u0301  café", "e\u0301 café"),
    ("zero_width_preserved", "a\u200bb", "a\u200bb"),
    ("vertical_whitespace", "a\v\fb", "a b"),
    ("crlf", "a\r\nb", "a b"),
]

candidate = Path(sys.argv[1])
source = candidate.read_text()
result = {"candidate_sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
          "case_count": len(CASES), "cases": [], "status": "valid"}
try:
    tree = ast.parse(source)
    result["ast_nodes"] = sum(1 for _ in ast.walk(tree))
    result["import_statements"] = sum(isinstance(n, (ast.Import, ast.ImportFrom)) for n in ast.walk(tree))
    ns = {"__name__": "fixture_candidate"}
    exec(compile(tree, str(candidate), "exec"), ns)
    normalize = ns["normalize"]
except Exception as exc:
    result.update(status="invalid", error=type(exc).__name__ + ": " + str(exc))
else:
    for case_id, value, expected in CASES:
        try:
            actual = normalize(value)
            passed = isinstance(actual, str) and actual == expected
            result["cases"].append({"id": case_id, "input": value, "expected": expected,
                                     "actual": actual, "passed": passed})
        except Exception as exc:
            result["cases"].append({"id": case_id, "input": value, "expected": expected,
                                     "error": type(exc).__name__ + ": " + str(exc), "passed": False})
result["passed"] = sum(c["passed"] for c in result["cases"])
result["failed"] = result["case_count"] - result["passed"]
print(json.dumps(result, ensure_ascii=False, sort_keys=True))

# Deliberately changed copy for an integrity negative control.

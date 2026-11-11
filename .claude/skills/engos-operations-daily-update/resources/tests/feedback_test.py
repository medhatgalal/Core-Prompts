"""Offline checks for the Feedback tab: lint, entry format, newest-first insert, first-entry replace, duplicate skip,
and that nothing outside the list is touched. No doc and no network.

    python3 feedback_test.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import feedback as fb  # noqa: E402

FAILS = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f": {detail}" if detail and not ok else ""))
    if not ok:
        FAILS.append(name)


def tab(*after):
    """A tab whose last paragraphs sit under 'Feedback so far'; indexes are consecutive."""
    texts = ["Feedback on the daily update", "Feedback so far", *after]
    at, paras = 1, []
    for t in texts:
        n = len(t) + 1
        paras.append({"startIndex": at, "endIndex": at + n, "paragraph": {"elements": [{"textRun": {"content": t + "\n"}}]}})
        at += n
    return {"documentTab": {"body": {"content": paras}}}


T = "t.x"
check("lint: clean line passes", fb.lint("The template is clear.") == [])
check("lint: link refused", bool(fb.lint("see https://a.b/c")))
check("lint: email refused", bool(fb.lint("ask a@b.com")))
check("lint: people-sensitive refused", bool(fb.lint("the candidate row is odd")))
check("lint: multi-line refused", bool(fb.lint("a\nb")))
check("lint: too long refused", bool(fb.lint("x" * 401)))
check("lint: empty refused", bool(fb.lint("  ")))

line = fb.entry("Wed Nov 11", "Scott", "The  template\nis clear.")
check("entry: format and whitespace", line == "Wed Nov 11, Scott: The template is clear.", line)

# first entry replaces 'None yet.' in place
r = fb.plan_add(tab("None yet."), T, line)
kinds = [next(iter(x)) for x in r]
check("first entry: deletes placeholder text then inserts", kinds[:2] == ["deleteContentRange", "insertText"], kinds)
check("first entry: no extra newline inserted", r[1]["insertText"]["text"] == line)

# later entry goes above the newest, with a newline, and bolds only date and name
old = "Tue Nov 10, Kyle: Draft missed a date."
r = fb.plan_add(tab(old), T, line)
ins = next(x["insertText"] for x in r if "insertText" in x)
check("later entry: inserted above newest", ins["text"] == line + "\n" and ins["location"]["index"] == tab(old)["documentTab"]["body"]["content"][2]["startIndex"])
bold = [x["updateTextStyle"] for x in r if "updateTextStyle" in x and x["updateTextStyle"]["textStyle"].get("bold")]
check("later entry: bold covers date and name only", len(bold) == 1 and bold[0]["range"]["endIndex"] - bold[0]["range"]["startIndex"] == len("Wed Nov 11, Scott:"), bold)
check("later entry: no deletes", not any("deleteContentRange" in x for x in r))
floor = tab(old)["documentTab"]["body"]["content"][2]["startIndex"]
starts = [(x[next(iter(x))].get("range") or x[next(iter(x))]["location"]).get("startIndex", x[next(iter(x))].get("location", {}).get("index"))
          for x in r]
check("nothing before the list is touched", all(v >= floor for v in starts), (floor, starts))

# duplicate and newest-first listing
check("duplicate is skipped", fb.plan_add(tab(line, old), T, line) is None)
check("list: newest first, placeholder hidden", fb.list_entries(tab(line, old)) == [line, old] and fb.list_entries(tab("None yet.")) == [])

# a restructured tab is refused, not guessed at
bad = {"documentTab": {"body": {"content": []}}}
try:
    fb.plan_add(bad, T, line)
    check("missing heading raises", False)
except ValueError:
    check("missing heading raises", True)

print(f"\n{len(FAILS)} failed" if FAILS else "\nall passed")
sys.exit(1 if FAILS else 0)

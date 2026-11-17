"""Read-only: open the department page in an own tab on CDP 9222, click every EXPAND, save page text.
Usage: dept_dump.py <out_txt>"""
import sys, time, datetime, pathlib, re
import sys as _s; _s.path.insert(0, str(pathlib.Path(__file__).parent))
from common import CFG
from playwright.sync_api import sync_playwright
URL = CFG["dept_url"]
LOG = pathlib.Path("crew/agents/roster/nav.log")
ts = lambda: datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(CFG["home_cdp"])
    page = b.contexts[0].new_page()
    try:
        with LOG.open("a") as f: f.write(f"{ts()} goto dept page (engineering-team)\n")
        page.goto(URL, timeout=120000); time.sleep(12)
        n = 0
        for _ in range(6):
            loc = page.get_by_text(re.compile(r"^\s*expand\s*$", re.I))
            if loc.count() == 0: break
            loc.first.click(); n += 1; time.sleep(4)
        print("expand clicked:", n); time.sleep(8)
        txt = page.inner_text("body")
        pathlib.Path(sys.argv[1]).write_text(txt)
        print("chars", len(txt), "remaining EXPAND:", txt.count("EXPAND"), "COLLAPSE:", txt.count("COLLAPSE"))
    finally:
        page.close()

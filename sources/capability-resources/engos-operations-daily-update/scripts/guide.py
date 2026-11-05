"""The 'Update guide' tab: template plus writing guidance. Text mirrors SKILL.md "Update guide tab".

  python3 guide.py DOC_ID [OWNER]     # add the tab to an E2E TEST doc (after Archive), pageless, with chips
"""
import sys

import dudoc as du
import modes as m

GITLAB_ASYNC = "https://handbook.gitlab.com/handbook/engineering/ai/ai-coding/how-we-work/async-updates/"
GITLAB_DRI = "https://handbook.gitlab.com/handbook/engineering/infrastructure-platforms/tenant-scale/organizations/dri/"
GITLAB_GROWTH = "https://handbook.gitlab.com/handbook/engineering/development/growth/engineering_dri/"
GITHUB_COMMS = "https://github.com/github/how-engineering-communicates"


def content(owner, overview_url, otitle):
    H1, H2, N = "HEADING_1", "HEADING_2", "NORMAL_TEXT"
    rows = [
        (f"Update guide ({owner})", H1),
        (f"Owner: {owner} · Back to {otitle}", N),
        ("Read this before writing a daily update. Your AI agent drafts from this template and these practices; "
         "you review, edit and publish.", N),
        ("Template", H2),
        ("Each initiative tab gets one section per day, newest first, in this order:", N),
        ("<Weekday Mon D, YYYY>  (date heading)", N),
        ("🟢 On track  |  🟡 At risk  |  🔴 Red  |  ⚪ Paused", N),
        ("Next milestone: <one thing>, <Weekday Mon D>", N),
        ("Confidence: Very confident", N),
        ("Progress: <up to 3 sentences on what changed and why it matters, each with a link>", N),
        ("Blocked on: <who, what, by when>, or None.", N),
        ("Green when: <the one thing that would make it green>  (only when not 🟢)", N),
        ("What each line means", H2),
        ("Status: set by the rules in the overview's status key, not by feel. A passed date is red; no date is at risk.", N),
        ("Next milestone: one outcome and one date with its weekday. Never \"this week\", \"soon\" or \"TBD\"; "
         "write \"No date set yet\" and the status becomes 🟡.", N),
        ("Confidence: your own call on whether the milestone lands on its date. Pick it from the dropdown. "
         "It never changes the status; if the two disagree, say why in Progress.", N),
        ("Progress: only what changed since the last update. Lead with what it means. If nothing changed, "
         "write \"No change since <date>.\"", N),
        ("Blocked on: name who, what and by when, so someone can act on it. Write \"None.\" when nothing is blocking.", N),
        ("Green when: the single condition that turns it green, so a reader knows what to help with.", N),
        ("Best practices", H2),
        ("Write for a leader outside your team. Spell out acronyms and internal names the first time on each tab.", N),
        ("Explain why a result matters, not only that it happened. A list of ticket numbers is not an update.", N),
        ("Flag blockers early, before they become critical.", N),
        ("Always give the next step, even if it is tentative.", N),
        ("When the colour changes, open Progress with the reason.", N),
        ("Link every claim to a source anyone in the company can open, on a short word like (Jira COM-994) or (merge request !455), never a raw URL. Never link email, chat or meeting notes; end that line \"(email)\", \"(chat)\" or \"(meeting notes)\" with no link.", N),
        ("Use absolute dates with the weekday. \"Today\" means US Eastern time.", N),
        ("Use the same template every time so readers can scan across tabs.", N),
        ("Status lives here, not in meetings. Read the doc before a meeting; meeting time goes to decisions.", N),
        ("Leave out people-sensitive items: candidate names, offers and pay, leave, health, performance.", N),
        ("Bad and good", H2),
        ("Bad: \"Completed !455, picking up COM-965 next.\"", N),
        ("Good: \"The Composer merge request merged, so internal release holds for Tue Nov 10 (merge request !455).\"", N),
        ("Sources", H2),
        ("Adapted from GitLab's weekly async update template, GitLab's guidance for initiative owners, GitLab's "
         "Growth engineering DRI page, and GitHub's How engineering communicates.", N),
    ]
    links = [(1, otitle, overview_url),
             (34, "weekly async update template", GITLAB_ASYNC),
             (34, "guidance for initiative owners", GITLAB_DRI),
             (34, "Growth engineering DRI page", GITLAB_GROWTH),
             (34, "How engineering communicates", GITHUB_COMMS)]
    return [r[0] for r in rows], [r[1] for r in rows], links


def add_guide(doc_id, owner="Scott"):
    doc = du.read_doc(doc_id)
    if any(t["tabProperties"]["title"].startswith(du.GUIDE) for t, p in du.all_tabs(doc) if p is None):
        return None
    n_top = len(doc["tabs"])
    r = du.batch(doc_id, [{"addDocumentTab": {"tabProperties": {"title": f"Update guide ({owner})", "index": n_top}}}], doc)
    tid = r["replies"][0]["addDocumentTab"]["tabProperties"]["tabId"]
    du.pageless(doc_id, [tid])
    lines, styles, links = content(owner, du.tab_url(doc_id, "t.0"), du.overview_title(du.read_doc(doc_id)))
    reqs = m._paras(tid, 1, lines, styles, links)
    k = next(i for i, x in enumerate(lines) if x.startswith("Status: set"))
    at = 1 + sum(du.utf16(x) + 1 for x in lines[:k])
    reqs.append({"updateTextStyle": {"range": {"startIndex": at, "endIndex": at + 7, "tabId": tid},
                                     "textStyle": {"bold": True}, "fields": "bold"}})
    du.batch(doc_id, reqs)
    du.chipify(doc_id, [tid])
    return tid


if __name__ == "__main__":
    print(add_guide(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "Scott"))

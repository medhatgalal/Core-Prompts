"""Settings for the Delivery Excellence prep. Every personal or org value lives in one local file, never in the repo.

    ~/.engos/delivery-excellence/settings.json   (override the folder with DELIVERY_EXCELLENCE_HOME)

backup.py keeps a private copy of that file in the person's own Google Drive under .engos/.
"""
import json
import os
import sys

HOME = os.environ.get("DELIVERY_EXCELLENCE_HOME") or os.path.expanduser("~/.engos/delivery-excellence")
PATH = os.path.join(HOME, "settings.json")
OUT = os.path.join(HOME, "out")
REQUIRED = ["leader_name", "org_name", "checkpoint_title", "jira_site", "jira_filter", "goals_container", "goals_root",
            "features_sheet", "group_field", "category_field", "current_release", "feature_card_releases",
            "feature_card_groups", "group_owners", "standing_work_categories", "standing_name_pattern",
            "doc_id", "readme_tab", "links", "how_to", "sections"]


def missing():
    if not os.path.isfile(PATH):
        return None
    d = json.load(open(PATH))
    return [k for k in REQUIRED if k not in d]


def load():
    m = missing()
    if m is None:
        sys.exit(f"No settings yet ({PATH}).\nFirst run: do the onboarding in the skill (it asks for your doc, Jira filter, "
                 "goals root and group owners), or restore from Drive with: python3 backup.py restore.\n"
                 "settings.example.json shows the shape.")
    if m:
        sys.exit(f"{PATH} is missing: {', '.join(m)}. Fill them in (see settings.example.json) or re-run onboarding.")
    return json.load(open(PATH))


def save(d):
    os.makedirs(HOME, exist_ok=True)
    json.dump(d, open(PATH, "w"), indent=2, ensure_ascii=False)

"""Org constants for the Jira scripts, read at run time from data/config.json ("jira" section). No Jira call."""
import json, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_j = json.load(open(os.path.join(ROOT, "data", "config.json")))["jira"]
HOST = _j["host"]
BASE = "https://" + HOST
F_OPEN = int(_j["filters"]["open"])
F_DASH = int(_j["filters"]["dashboard"])
CF_GROUP = _j["fields"]["group"]          # e.g. customfield_NNNNN
CF_MR = _j["fields"]["mr_link"]           # e.g. customfield_NNNNN
SCOPE_GROUPS = set(_j["scope_group_values"])
ENV_EMAIL = _j["auth"]["email_env"]       # NAMES of environment variables only; the values are never read into logs or files
ENV_TOKEN = _j["auth"]["token_env"]
API_BASE = (_j.get("api_base") or BASE).rstrip("/")   # set to https://api.atlassian.com/ex/jira/<cloudId> only for a scoped token
INCIDENT_PROJECTS = list(_j.get("incident_projects", []))   # Jira project keys whose issues are counted as incidents (own extract, own files)
CF_TEAM = _j["fields"].get("team", "")                      # Atlassian Team field: an object with the team name (an org unit, not a person)
GROUP_COL = _j["group_field_column"]          # name of the Group column in the extract CSVs
CF_SBU = _j["fields"]["sbu"]                  # SBU select field
CF_WC = _j["fields"]["work_category"]         # Work Category select field
GROUP_ALIASES = dict(_j.get("group_aliases", {}))   # former Group name -> current Group name (a lineage)
KNOWN_RULINGS = [tuple(x) for x in _j.get("known_rulings", [])]   # (date, field, from, to, ruling text) for the bulk-event report
UI_FILTER_NAME = _j.get("ui_filter_name", "")
TEAM_ALIASES = dict(_j.get("team_aliases", {}))     # Jira Team name -> roster Team name
def cfnum(cf): return cf.split("_", 1)[1]           # customfield_12345 -> 12345
def jql_cf(cf): return "cf[%s]" % cfnum(cf)         # JQL spelling of a custom field

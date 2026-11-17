"""Mask secret-looking query parameter values for tools/ro log lines (AC38). Keeps method, path, parameter names, status.
Masks the value when the NAME looks secret-bearing or the VALUE is credential-shaped. Ordinary filters (dates, usernames, ids) stay."""
import re
from urllib.parse import quote

SECRET_SEGMENTS = {"auth", "authorization", "authentication", "key", "sig", "signature", "session", "cookie", "bearer", "pwd", "apikey", "cred", "creds"}
SECRET_SUBSTR = ("token", "secret", "passw", "credential", "apikey", "privatekey", "accesskey")


def _name_is_secret(name):
    low = name.lower()
    segs = [x for x in re.split(r"[_\-\[\]\.]+", low) if x]
    if any(x in SECRET_SEGMENTS for x in segs):
        return True
    squashed = re.sub(r"[_\-\[\]\.]", "", low)
    return any(t in squashed for t in SECRET_SUBSTR)


# credential-shaped values: vendor prefixes, JWT, Authorization-style, long mixed-case alphanumerics (not plain hex such as commit SHAs)
PREFIX_RE = re.compile(r"^(glpat-|gldt-|glrt-|glcbt-|glptt-|glft-|gloas-|glsoat-|ghp_|gho_|ghu_|ghs_|ghr_|github_pat_|xox[abprs]-|sk-|AKIA|ASIA|AIza|ya29\.|eyJ)", re.I)
BEARER_RE = re.compile(r"^(bearer|basic|token)(\s|%20|\+)", re.I)
LONG_RE = re.compile(r"^[A-Za-z0-9_\-+/=.]{24,}$")
MASK = "***"


def _credential_shaped(v):
    if PREFIX_RE.match(v) or BEARER_RE.match(v):
        return True
    if LONG_RE.match(v) and not re.fullmatch(r"[0-9a-fA-F]+", v):
        has = (bool(re.search(r"[a-z]", v)), bool(re.search(r"[A-Z]", v)), bool(re.search(r"[0-9]", v)))
        if sum(has) >= 3:
            return True
    return False


def mask_path(path):
    """Return path with secret-looking query values replaced by ***; names are kept."""
    if "?" not in path:
        return path
    base, q = path.split("?", 1)
    out = []
    for part in q.split("&"):
        if "=" not in part:
            out.append(part); continue
        name, val = part.split("=", 1)
        if val and (_name_is_secret(name) or _credential_shaped(val)):
            out.append(f"{name}={MASK}")
        else:
            out.append(part)
    return base + "?" + "&".join(out)


def line_has_secret(line):
    """True if any query value on a tab-separated log line would be masked (used by the scan; never returns the value)."""
    for field in line.rstrip("\n").split("\t"):
        if "?" in field and mask_path(field) != field:
            return True
    return False

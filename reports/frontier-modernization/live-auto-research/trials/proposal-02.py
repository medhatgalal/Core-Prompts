import re


def normalize(value):
    return re.sub(r"\s+", " ", value).strip()

"""PUBLIC contract: only an owner may cancel, and settled orders cannot cancel."""


def can_cancel(is_owner, status):
    if is_owner:
        return status != "settled"
    return False

"""Public reference: single-threaded expiring leases."""


class LeaseBook:
    def __init__(self):
        self._leases = {}

    def acquire(self, key, owner, now, ttl):
        if ttl <= 0:
            raise ValueError("ttl must be positive")
        current = self._leases.get(key)
        if current is not None and now < current[1]:
            return False
        self._leases[key] = (owner, now + ttl)
        return True

    def renew(self, key, owner, now, ttl):
        if ttl <= 0:
            raise ValueError("ttl must be positive")
        current = self._leases.get(key)
        if current is None or current[0] != owner or now >= current[1]:
            return False
        self._leases[key] = (owner, now + ttl)
        return True

    def release(self, key, owner):
        current = self._leases.get(key)
        if current is None or current[0] != owner:
            return False
        del self._leases[key]
        return True

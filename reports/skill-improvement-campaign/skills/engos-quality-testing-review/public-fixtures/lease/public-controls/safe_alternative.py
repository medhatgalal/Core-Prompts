"""Public safe control: different representation, same observable contract."""


class LeaseBook:
    def __init__(self):
        self.entries = []

    def _find(self, key):
        return next((row for row in self.entries if row[0] == key), None)

    def acquire(self, key, owner, now, ttl):
        if ttl <= 0:
            raise ValueError("positive duration required")
        row = self._find(key)
        if row and row[2] > now:
            return False
        if row:
            self.entries.remove(row)
        self.entries.append([key, owner, now + ttl])
        return True

    def renew(self, key, owner, now, ttl):
        if ttl <= 0:
            raise ValueError("positive duration required")
        row = self._find(key)
        if row and row[1] == owner and row[2] > now:
            row[2] = now + ttl
            return True
        return False

    def release(self, key, owner):
        row = self._find(key)
        if row and row[1] == owner:
            self.entries.remove(row)
            return True
        return False

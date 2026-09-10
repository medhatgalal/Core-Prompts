"""PUBLIC reference: local SQLite integration boundary, no external service."""
import sqlite3


def initialize(path):
    db = sqlite3.connect(path)
    try:
        db.execute("CREATE TABLE orders (key TEXT PRIMARY KEY, cents INTEGER NOT NULL)")
        db.commit()
    finally:
        db.close()


def create_order(path, key, cents):
    if cents <= 0:
        raise ValueError("positive amount required")
    db = sqlite3.connect(path)
    try:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT cents FROM orders WHERE key = ?", (key,)).fetchone()
        if row is not None:
            if row[0] != cents:
                raise ValueError("idempotency key conflict")
        else:
            db.execute("INSERT INTO orders VALUES (?, ?)", (key, cents))
        db.commit()
        return {"key": key, "cents": cents}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

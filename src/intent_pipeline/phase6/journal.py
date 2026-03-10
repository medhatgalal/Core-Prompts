"""Phase-6 append-only deterministic execution journal."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable

from intent_pipeline.phase6.contracts import ExecutionJournalRecord


@dataclass(frozen=True, slots=True)
class JournalLookup:
    relative_path: str
    records: tuple[ExecutionJournalRecord, ...]

    @property
    def latest(self) -> ExecutionJournalRecord | None:
        return self.records[-1] if self.records else None


class ExecutionJournal:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def relative_path_for(self, idempotency_key: str) -> str:
        import hashlib
        digest = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()
        return f"{digest}.jsonl"

    def lookup(self, idempotency_key: str) -> JournalLookup:
        relative_path = self.relative_path_for(idempotency_key)
        absolute_path = self.root / relative_path
        if not absolute_path.exists():
            return JournalLookup(relative_path=relative_path, records=())
        records: list[ExecutionJournalRecord] = []
        for line in absolute_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            records.append(ExecutionJournalRecord(**payload))
        return JournalLookup(relative_path=relative_path, records=tuple(records))

    def append(self, record: ExecutionJournalRecord) -> str:
        relative_path = self.relative_path_for(record.idempotency_key)
        absolute_path = self.root / relative_path
        with absolute_path.open("a", encoding="utf-8") as handle:
            handle.write(record.to_json())
            handle.write("\n")
        return relative_path

    def already_recorded(self, idempotency_key: str, envelope_sha256: str) -> ExecutionJournalRecord | None:
        lookup = self.lookup(idempotency_key)
        for record in reversed(lookup.records):
            if record.envelope_sha256 == envelope_sha256 and record.decision.value in {"SIMULATED", "EXECUTED"}:
                return record
        return None


__all__ = ["ExecutionJournal", "JournalLookup"]

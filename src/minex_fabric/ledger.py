from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .io_utils import canonical_json, load_jsonl, sha256_text, write_jsonl


@dataclass
class LedgerEvent:
    seq: int
    event_type: str
    payload: Dict[str, Any]
    prev_hash: str
    event_hash: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "seq": self.seq,
            "event_type": self.event_type,
            "payload": self.payload,
            "prev_hash": self.prev_hash,
            "event_hash": self.event_hash,
        }


class HashLedger:
    def __init__(self) -> None:
        self.events: List[LedgerEvent] = []

    def append(self, event_type: str, payload: Dict[str, Any]) -> LedgerEvent:
        seq = len(self.events)
        prev_hash = self.events[-1].event_hash if self.events else "0" * 64
        body = {"seq": seq, "event_type": event_type, "payload": payload, "prev_hash": prev_hash}
        event_hash = sha256_text(canonical_json(body))
        event = LedgerEvent(seq, event_type, payload, prev_hash, event_hash)
        self.events.append(event)
        return event

    def write(self, path: str | Path) -> None:
        write_jsonl(path, [e.as_dict() for e in self.events])

    @staticmethod
    def verify_rows(rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        prev = "0" * 64
        count = 0
        errors: List[str] = []
        head = prev
        for expected_seq, row in enumerate(rows):
            body = {
                "seq": row.get("seq"),
                "event_type": row.get("event_type"),
                "payload": row.get("payload"),
                "prev_hash": row.get("prev_hash"),
            }
            actual = sha256_text(canonical_json(body))
            if row.get("seq") != expected_seq:
                errors.append(f"row {expected_seq}: sequence mismatch")
            if row.get("prev_hash") != prev:
                errors.append(f"row {expected_seq}: previous hash mismatch")
            if row.get("event_hash") != actual:
                errors.append(f"row {expected_seq}: event hash mismatch")
            prev = row.get("event_hash", "")
            head = prev
            count += 1
        return {"valid": not errors, "event_count": count, "errors": errors, "head_hash": head}

    @classmethod
    def verify_file(cls, path: str | Path) -> Dict[str, Any]:
        return cls.verify_rows(load_jsonl(path))

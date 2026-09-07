#!/usr/bin/env python3
"""Verify JSON readability and every reference evidence ledger."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from minex_fabric.ledger import HashLedger  # noqa: E402


def main() -> int:
    json_count = 0
    ledger_count = 0
    errors: list[str] = []
    for path in ROOT.rglob("*.json"):
        if "validation" in path.relative_to(ROOT).parts:
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
            json_count += 1
        except Exception as exc:
            errors.append(f"JSON {path.relative_to(ROOT)}: {exc}")
    for path in ROOT.rglob("evidence_ledger.jsonl"):
        result = HashLedger.verify_file(path)
        ledger_count += 1
        if not result.get("valid"):
            errors.append(f"LEDGER {path.relative_to(ROOT)}: {result}")
    summary = {"json_files": json_count, "evidence_ledgers": ledger_count, "valid": not errors, "errors": errors}
    print(json.dumps(summary, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())

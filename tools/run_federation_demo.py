#!/usr/bin/env python3
"""Run a real localhost capability-borrowing round trip.

This demo opens only an ephemeral loopback port. Execution is restricted by a
bearer credential and an HMAC-signed lease. It does not move money or expose an
internet-facing service.
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from minex_fabric.authorization import issue_lease  # noqa: E402
from minex_fabric.federation import CapabilityNode, RemoteNodeClient  # noqa: E402
from minex_fabric.io_utils import write_json  # noqa: E402
from minex_fabric.models import TaskContract  # noqa: E402
from minex_fabric.registry import CapabilityRegistry  # noqa: E402


def run_demo(output: Path) -> dict:
    bearer = "minex-local-demo-bearer"
    secret = "minex-local-demo-lease-secret"
    registry = CapabilityRegistry.from_directory(ROOT / "examples" / "node_capabilities" / "utility")
    node = CapabilityNode(
        registry,
        node_id="node-utility",
        bearer_token=bearer,
        lease_secret=secret,
        allow_execution=True,
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), node.handler_class())
    port = int(server.server_address[1])
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = RemoteNodeClient(f"http://127.0.0.1:{port}", bearer_token=bearer)
        task = TaskContract(
            task_id="federated-http-demo",
            purpose="Borrow a bounded hash function from an authorized node",
            operation="data.hash.sha256",
            work_units=3,
            input_bytes=24,
            input_data_class="PUBLIC",
            inputs={"data": "authorized federation demo"},
            requester="local-demo-owner",
        )
        lease_payload = {
            "lease_id": "lease-federated-reference",
            "principal": "local-demo-owner",
            "node_ids": ["node-utility"],
            "capability_ids": ["cap.hash.federated"],
            "scopes": ["federation:borrow"],
            "data_classes": ["PUBLIC"],
            "max_calls": 2,
            "expires_at_epoch": int(time.time()) + 300,
        }
        lease_token = issue_lease(lease_payload, secret)
        result = {
            "health": client.health(),
            "manifest": client.manifest(),
            "quote": client.quote(task),
            "execution": client.execute(task, "cap.hash.federated", lease_token),
            "boundary": {
                "transport": "localhost only",
                "real_funds_moved": False,
                "automatic_external_action_authority": 0,
                "internet_grade_security_certified": False,
            },
        }
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "outputs" / "federation_demo" / "result.json",
    )
    args = parser.parse_args()
    result = run_demo(args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

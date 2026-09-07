from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional

from .authorization import verify_lease
from .executors import execute_capability
from .io_utils import canonical_json, sha256_text
from .market import create_quote
from .models import CapabilityManifest, TaskContract
from .registry import CapabilityRegistry


class RemoteNodeError(RuntimeError):
    pass


class RemoteNodeClient:
    def __init__(self, endpoint: str, *, bearer_token: str = "", timeout: float = 10.0) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.bearer_token = bearer_token
        self.timeout = timeout

    def _request(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.endpoint + path, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        if self.bearer_token:
            req.add_header("Authorization", f"Bearer {self.bearer_token}")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RemoteNodeError(f"remote node HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')}") from exc
        except urllib.error.URLError as exc:
            raise RemoteNodeError(f"remote node unavailable: {exc}") from exc

    def health(self) -> Dict[str, Any]:
        return self._request("GET", "/health")

    def manifest(self) -> Dict[str, Any]:
        return self._request("GET", "/manifest")

    def quote(self, task: TaskContract) -> Dict[str, Any]:
        return self._request("POST", "/quote", {"task": task.as_dict()})

    def execute(self, task: TaskContract, capability_id: str, lease_token: str) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/execute",
            {"task": task.as_dict(), "capability_id": capability_id, "lease_token": lease_token},
        )


class CapabilityNode:
    def __init__(
        self,
        registry: CapabilityRegistry,
        *,
        node_id: str,
        bearer_token: str,
        lease_secret: str,
        allow_execution: bool,
    ) -> None:
        self.registry = registry
        self.node_id = node_id
        self.bearer_token = bearer_token
        self.lease_secret = lease_secret
        self.allow_execution = allow_execution
        self.calls: Dict[str, int] = {}

    def handler_class(self):
        node = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "MINEXCapabilityNode/1.0"

            def _write(self, status: int, payload: Dict[str, Any]) -> None:
                data = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _json(self) -> Dict[str, Any]:
                length = int(self.headers.get("Content-Length", "0"))
                return json.loads(self.rfile.read(length).decode("utf-8")) if length else {}

            def _bearer_ok(self) -> bool:
                return self.headers.get("Authorization", "") == f"Bearer {node.bearer_token}"

            def log_message(self, fmt: str, *args: Any) -> None:
                return

            def do_GET(self):
                if self.path == "/health":
                    self._write(200, {"status": "ok", "node_id": node.node_id, "allow_execution": node.allow_execution})
                    return
                if self.path == "/manifest":
                    self._write(
                        200,
                        {
                            "node_id": node.node_id,
                            "capabilities": [m.as_dict() for m in node.registry.all()],
                            "execution_requires_bearer_and_lease": True,
                        },
                    )
                    return
                self._write(404, {"error": "not found"})

            def do_POST(self):
                try:
                    body = self._json()
                    if self.path == "/quote":
                        task = TaskContract.from_dict(body["task"])
                        quotes = [
                            create_quote(m, task, expires_at_epoch=int(time.time()) + 300).as_dict()
                            for m in node.registry.matching(task.operation)
                        ]
                        self._write(200, {"node_id": node.node_id, "quotes": quotes})
                        return
                    if self.path == "/execute":
                        if not node.allow_execution:
                            self._write(403, {"error": "execution disabled"})
                            return
                        if not self._bearer_ok():
                            self._write(401, {"error": "invalid bearer token"})
                            return
                        lease = verify_lease(str(body.get("lease_token", "")), node.lease_secret)
                        cap_id = str(body["capability_id"])
                        if cap_id not in lease.get("capability_ids", []) and "*" not in lease.get("capability_ids", []):
                            self._write(403, {"error": "capability not granted by lease"})
                            return
                        if node.node_id not in lease.get("node_ids", []) and "*" not in lease.get("node_ids", []):
                            self._write(403, {"error": "node not granted by lease"})
                            return
                        lease_id = str(lease.get("lease_id", "unknown"))
                        node.calls[lease_id] = node.calls.get(lease_id, 0) + 1
                        if node.calls[lease_id] > int(lease.get("max_calls", 1)):
                            self._write(429, {"error": "lease call limit exceeded"})
                            return
                        task = TaskContract.from_dict(body["task"])
                        manifest = node.registry.get(cap_id)
                        if task.operation != manifest.operation:
                            self._write(400, {"error": "operation mismatch"})
                            return
                        result = execute_capability(manifest, task)
                        receipt_body = {
                            "node_id": node.node_id,
                            "lease_id": lease_id,
                            "capability_id": cap_id,
                            "task_id": task.task_id,
                            "output_hash": sha256_text(canonical_json(result["output"])),
                            "execution_state": result["execution_state"],
                        }
                        self._write(200, {"result": result, "receipt": {**receipt_body, "receipt_hash": sha256_text(canonical_json(receipt_body))}})
                        return
                    self._write(404, {"error": "not found"})
                except Exception as exc:
                    self._write(400, {"error": type(exc).__name__, "message": str(exc)})

        return Handler


def serve_node(
    registry: CapabilityRegistry,
    *,
    node_id: str,
    host: str,
    port: int,
    bearer_token: str,
    lease_secret: str,
    allow_execution: bool,
) -> None:
    if host not in {"127.0.0.1", "localhost", "::1"} and not bearer_token:
        raise ValueError("external bind requires a bearer token")
    if allow_execution and (not bearer_token or not lease_secret):
        raise ValueError("execution requires bearer token and lease secret")
    node = CapabilityNode(
        registry,
        node_id=node_id,
        bearer_token=bearer_token,
        lease_secret=lease_secret,
        allow_execution=allow_execution,
    )
    server = ThreadingHTTPServer((host, port), node.handler_class())
    print(json.dumps({"status": "serving", "host": host, "port": port, "node_id": node_id, "allow_execution": allow_execution}))
    server.serve_forever()

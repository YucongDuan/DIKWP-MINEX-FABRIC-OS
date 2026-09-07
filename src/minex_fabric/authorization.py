from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any, Dict, Iterable, Tuple

from .io_utils import canonical_json
from .models import AuthorizationContext, CapabilityManifest, TaskContract


def check_authorization(
    manifest: CapabilityManifest,
    task: TaskContract,
    auth: AuthorizationContext,
    *,
    now_epoch: int | None = None,
) -> Tuple[bool, list[str], Dict[str, bool]]:
    now = int(time.time()) if now_epoch is None else int(now_epoch)
    checks: Dict[str, bool] = {}
    checks["lease_not_expired"] = auth.expires_at_epoch >= now
    checks["node_allowed"] = manifest.node_id in auth.allowed_nodes or "*" in auth.allowed_nodes
    checks["data_class_allowed_by_auth"] = task.input_data_class in auth.allowed_data_classes or "*" in auth.allowed_data_classes
    checks["data_class_allowed_by_capability"] = (
        task.input_data_class in manifest.allowed_data_classes or "*" in manifest.allowed_data_classes
    )
    scope_set = set(auth.scopes)
    checks["required_scopes_present"] = all(s in scope_set or "*" in scope_set for s in manifest.required_scopes)
    checks["paid_route_authorized"] = (
        manifest.monetary_cost_base <= 0 and manifest.monetary_cost_per_unit <= 0
    ) or auth.allow_paid
    reasons = [k for k, ok in checks.items() if not ok]
    return all(checks.values()), reasons, checks


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def issue_lease(payload: Dict[str, Any], secret: str) -> str:
    header = {"alg": "HS256", "typ": "MINEX-LEASE", "v": 1}
    h = _b64(canonical_json(header).encode("utf-8"))
    p = _b64(canonical_json(payload).encode("utf-8"))
    sig = hmac.new(secret.encode("utf-8"), f"{h}.{p}".encode("ascii"), hashlib.sha256).digest()
    return f"{h}.{p}.{_b64(sig)}"


def verify_lease(token: str, secret: str, *, now_epoch: int | None = None) -> Dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("invalid lease token")
    h, p, s = parts
    expected = hmac.new(secret.encode("utf-8"), f"{h}.{p}".encode("ascii"), hashlib.sha256).digest()
    if not hmac.compare_digest(expected, _unb64(s)):
        raise ValueError("invalid lease signature")
    payload = json.loads(_unb64(p).decode("utf-8"))
    now = int(time.time()) if now_epoch is None else int(now_epoch)
    if int(payload.get("expires_at_epoch", 0)) < now:
        raise ValueError("lease expired")
    return payload

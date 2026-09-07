from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List

from .energy import estimate_resources
from .io_utils import canonical_json, sha256_text
from .models import CapabilityManifest, TaskContract


@dataclass
class MarketQuote:
    quote_id: str
    provider_id: str
    node_id: str
    capability_id: str
    task_id: str
    resource_vector: Dict[str, Any]
    price: float
    currency: str
    expires_at_epoch: int
    terms_hash: str

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def create_quote(manifest: CapabilityManifest, task: TaskContract, *, expires_at_epoch: int, currency: str = "USD") -> MarketQuote:
    vector = estimate_resources(manifest, task)
    body = {
        "provider_id": manifest.provider_id,
        "node_id": manifest.node_id,
        "capability_id": manifest.capability_id,
        "task_id": task.task_id,
        "resource_vector": vector.as_dict(),
        "currency": currency,
        "expires_at_epoch": int(expires_at_epoch),
    }
    terms_hash = sha256_text(canonical_json(body))
    return MarketQuote(
        quote_id=f"quote-{terms_hash[:16]}",
        provider_id=manifest.provider_id,
        node_id=manifest.node_id,
        capability_id=manifest.capability_id,
        task_id=task.task_id,
        resource_vector=vector.as_dict(),
        price=vector.monetary_cost,
        currency=currency,
        expires_at_epoch=int(expires_at_epoch),
        terms_hash=terms_hash,
    )


def create_dry_run_settlement(quote: MarketQuote, output_hash: str, success: bool) -> Dict[str, Any]:
    body = {
        "quote_id": quote.quote_id,
        "terms_hash": quote.terms_hash,
        "output_hash": output_hash,
        "success": bool(success),
        "amount": quote.price if success else 0.0,
        "currency": quote.currency,
        "payment_state": "DRY_RUN_SETTLED" if success else "DRY_RUN_VOID",
        "real_funds_moved": False,
    }
    return {**body, "settlement_hash": sha256_text(canonical_json(body))}

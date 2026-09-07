from __future__ import annotations

from dataclasses import replace
from typing import Iterable, List

from .models import CapabilityManifest, ResourceVector, TaskContract


MINIMIZE_FIELDS = {
    "physical_energy_j",
    "monetary_cost",
    "latency_ms",
    "human_minutes",
    "data_egress_bytes",
    "semantic_loss",
    "privacy_risk",
    "irreversibility",
}
MAXIMIZE_FIELDS = {"expected_quality", "reliability"}


def estimate_resources(manifest: CapabilityManifest, task: TaskContract) -> ResourceVector:
    units = max(0.0, float(task.work_units))
    data_mb = max(0.0, float(task.input_bytes)) / 1_000_000.0
    remote = manifest.mode in {"REMOTE_API", "FEDERATED_NODE", "BROWSER"}
    network_energy = manifest.network_energy_per_mb_j * data_mb if remote else 0.0
    data_egress = task.input_bytes if remote else 0
    energy = manifest.base_energy_j + manifest.energy_per_work_unit_j * units + network_energy
    latency = manifest.base_latency_ms + manifest.latency_per_work_unit_ms * units
    cost = manifest.monetary_cost_base + manifest.monetary_cost_per_unit * units
    return ResourceVector(
        physical_energy_j=round(energy, 6),
        monetary_cost=round(cost, 6),
        latency_ms=round(latency, 6),
        human_minutes=round(manifest.human_minutes_base, 6),
        data_egress_bytes=int(data_egress),
        semantic_loss=manifest.semantic_loss,
        privacy_risk=manifest.privacy_risk,
        irreversibility=manifest.irreversibility,
        expected_quality=manifest.expected_quality,
        reliability=manifest.reliability,
        evidence_class="DECLARED_OR_MODELLED",
    )


def _no_worse(a: ResourceVector, b: ResourceVector, field: str) -> bool:
    av, bv = getattr(a, field), getattr(b, field)
    if field in MAXIMIZE_FIELDS:
        return av >= bv
    return av <= bv


def _strictly_better(a: ResourceVector, b: ResourceVector, field: str) -> bool:
    av, bv = getattr(a, field), getattr(b, field)
    if field in MAXIMIZE_FIELDS:
        return av > bv
    return av < bv


def dominates(a: ResourceVector, b: ResourceVector, fields: Iterable[str] | None = None) -> bool:
    fields = list(fields or [
        "physical_energy_j",
        "monetary_cost",
        "latency_ms",
        "human_minutes",
        "data_egress_bytes",
        "semantic_loss",
        "privacy_risk",
        "irreversibility",
        "expected_quality",
        "reliability",
    ])
    return all(_no_worse(a, b, f) for f in fields) and any(_strictly_better(a, b, f) for f in fields)


def pareto_frontier(items: List[tuple[str, ResourceVector]]) -> List[str]:
    frontier: List[str] = []
    for i, (item_id, vector) in enumerate(items):
        if not any(j != i and dominates(other, vector) for j, (_, other) in enumerate(items)):
            frontier.append(item_id)
    return sorted(frontier)


def combine_vectors(vectors: List[ResourceVector], *, parallel: bool) -> ResourceVector:
    if not vectors:
        raise ValueError("cannot combine empty resource vectors")
    return ResourceVector(
        physical_energy_j=sum(v.physical_energy_j for v in vectors),
        monetary_cost=sum(v.monetary_cost for v in vectors),
        latency_ms=max(v.latency_ms for v in vectors) if parallel else sum(v.latency_ms for v in vectors),
        human_minutes=sum(v.human_minutes for v in vectors),
        data_egress_bytes=sum(v.data_egress_bytes for v in vectors),
        semantic_loss=max(v.semantic_loss for v in vectors),
        privacy_risk=max(v.privacy_risk for v in vectors),
        irreversibility=max(v.irreversibility for v in vectors),
        expected_quality=min(v.expected_quality for v in vectors),
        reliability=min(v.reliability for v in vectors),
        evidence_class="COMPOSED",
    )

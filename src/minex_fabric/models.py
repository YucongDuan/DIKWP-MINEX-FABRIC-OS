from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Mapping, Optional


EXECUTION_MODES = {
    "MODEL_NATIVE",
    "GENERATED_CODE",
    "LOCAL_API",
    "REMOTE_API",
    "BROWSER",
    "GUI",
    "FEDERATED_NODE",
    "HUMAN",
}


@dataclass(frozen=True)
class ResourceVector:
    """Non-aggregated execution resource and risk vector.

    Physical energy is never silently converted into money, latency, human
    time, privacy risk, or semantic loss.  Selection is constraint-first and
    Pareto/lexicographic unless a caller explicitly supplies a scalar policy.
    """

    physical_energy_j: float
    monetary_cost: float
    latency_ms: float
    human_minutes: float
    data_egress_bytes: int
    semantic_loss: float
    privacy_risk: float
    irreversibility: float
    expected_quality: float
    reliability: float
    evidence_class: str = "DECLARED"

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def objective_tuple(self, order: List[str]) -> tuple:
        d = self.as_dict()
        return tuple(d[k] for k in order)


@dataclass(frozen=True)
class CapabilityManifest:
    capability_id: str
    name: str
    operation: str
    mode: str
    provider_id: str
    node_id: str
    version: str
    enabled: bool = True
    description: str = ""
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    required_scopes: List[str] = field(default_factory=list)
    allowed_data_classes: List[str] = field(default_factory=lambda: ["PUBLIC"])
    base_energy_j: float = 0.0
    energy_per_work_unit_j: float = 0.0
    network_energy_per_mb_j: float = 0.0
    base_latency_ms: float = 0.0
    latency_per_work_unit_ms: float = 0.0
    monetary_cost_base: float = 0.0
    monetary_cost_per_unit: float = 0.0
    human_minutes_base: float = 0.0
    expected_quality: float = 1.0
    reliability: float = 1.0
    semantic_loss: float = 0.0
    privacy_risk: float = 0.0
    irreversibility: float = 0.0
    internalizable: bool = False
    license: str = "UNSPECIFIED"
    endpoint: Optional[str] = None
    executor: str = "builtin"
    tags: List[str] = field(default_factory=list)
    lineage: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.mode not in EXECUTION_MODES:
            raise ValueError(f"unsupported execution mode: {self.mode}")
        for name in ("expected_quality", "reliability", "semantic_loss", "privacy_risk", "irreversibility"):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0,1]")

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "CapabilityManifest":
        return cls(**dict(value))


@dataclass(frozen=True)
class TaskContract:
    task_id: str
    purpose: str
    operation: str
    work_units: float = 1.0
    input_bytes: int = 0
    input_data_class: str = "PUBLIC"
    inputs: Dict[str, Any] = field(default_factory=dict)
    output_requirements: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    selection_order: List[str] = field(
        default_factory=lambda: [
            "physical_energy_j",
            "monetary_cost",
            "latency_ms",
            "human_minutes",
            "data_egress_bytes",
        ]
    )
    parallel_group: Optional[str] = None
    subtasks: List[Dict[str, Any]] = field(default_factory=list)
    requester: str = "anonymous"

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "TaskContract":
        return cls(**dict(value))


@dataclass(frozen=True)
class AuthorizationContext:
    principal: str
    scopes: List[str]
    allowed_nodes: List[str]
    allowed_data_classes: List[str]
    expires_at_epoch: int
    max_calls: int = 100
    allow_paid: bool = False
    max_payment: float = 0.0
    lease_id: str = "local-lease"

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "AuthorizationContext":
        return cls(**dict(value))


@dataclass
class CandidateEvaluation:
    capability_id: str
    operation: str
    feasible: bool
    resource_vector: Optional[ResourceVector]
    rejection_reasons: List[str] = field(default_factory=list)
    authorization_checks: Dict[str, bool] = field(default_factory=dict)
    provider_id: str = ""
    node_id: str = ""
    mode: str = ""

    def as_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.resource_vector is not None:
            d["resource_vector"] = self.resource_vector.as_dict()
        return d


@dataclass
class PlanDecision:
    task_id: str
    status: str
    selected_capability_id: Optional[str]
    selected_resource_vector: Optional[ResourceVector]
    pareto_frontier: List[str]
    candidates: List[CandidateEvaluation]
    selection_order: List[str]
    rationale: List[str]
    permission_bypass_attempted: bool = False
    scalar_aggregate_used: bool = False

    def as_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status,
            "selected_capability_id": self.selected_capability_id,
            "selected_resource_vector": self.selected_resource_vector.as_dict() if self.selected_resource_vector else None,
            "pareto_frontier": self.pareto_frontier,
            "candidates": [c.as_dict() for c in self.candidates],
            "selection_order": self.selection_order,
            "rationale": self.rationale,
            "permission_bypass_attempted": self.permission_bypass_attempted,
            "scalar_aggregate_used": self.scalar_aggregate_used,
        }

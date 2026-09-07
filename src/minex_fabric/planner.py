from __future__ import annotations

import time
from typing import Iterable, List, Optional

from .authorization import check_authorization
from .energy import estimate_resources, pareto_frontier
from .models import (
    AuthorizationContext,
    CandidateEvaluation,
    CapabilityManifest,
    PlanDecision,
    ResourceVector,
    TaskContract,
)
from .registry import CapabilityRegistry


class CapabilityPlanner:
    """Constraint-first, non-aggregated capability planner."""

    def __init__(self, registry: CapabilityRegistry) -> None:
        self.registry = registry

    def evaluate_candidate(
        self,
        manifest: CapabilityManifest,
        task: TaskContract,
        auth: AuthorizationContext,
        *,
        now_epoch: Optional[int] = None,
    ) -> CandidateEvaluation:
        vector = estimate_resources(manifest, task)
        authorized, auth_reasons, checks = check_authorization(manifest, task, auth, now_epoch=now_epoch)
        reasons = list(auth_reasons)
        c = task.constraints

        if manifest.mode in set(c.get("forbidden_modes", [])):
            reasons.append("mode_forbidden")
        allowed_modes = c.get("allowed_modes")
        if allowed_modes and manifest.mode not in set(allowed_modes):
            reasons.append("mode_not_allowed")
        if c.get("require_local", False) and manifest.mode in {"REMOTE_API", "BROWSER", "FEDERATED_NODE"}:
            reasons.append("local_execution_required")
        if vector.expected_quality < float(c.get("min_quality", 0.0)):
            reasons.append("quality_below_minimum")
        if vector.reliability < float(c.get("min_reliability", 0.0)):
            reasons.append("reliability_below_minimum")
        if vector.semantic_loss > float(c.get("max_semantic_loss", 1.0)):
            reasons.append("semantic_loss_above_maximum")
        if vector.privacy_risk > float(c.get("max_privacy_risk", 1.0)):
            reasons.append("privacy_risk_above_maximum")
        if vector.irreversibility > float(c.get("max_irreversibility", 1.0)):
            reasons.append("irreversibility_above_maximum")
        if vector.physical_energy_j > float(c.get("max_energy_j", float("inf"))):
            reasons.append("energy_budget_exceeded")
        if vector.monetary_cost > float(c.get("max_cost", float("inf"))):
            reasons.append("monetary_budget_exceeded")
        if vector.latency_ms > float(c.get("max_latency_ms", float("inf"))):
            reasons.append("deadline_exceeded")
        if vector.monetary_cost > auth.max_payment and vector.monetary_cost > 0:
            reasons.append("lease_payment_limit_exceeded")
        feasible = authorized and not reasons
        return CandidateEvaluation(
            capability_id=manifest.capability_id,
            operation=manifest.operation,
            feasible=feasible,
            resource_vector=vector,
            rejection_reasons=sorted(set(reasons)),
            authorization_checks=checks,
            provider_id=manifest.provider_id,
            node_id=manifest.node_id,
            mode=manifest.mode,
        )

    def plan(
        self,
        task: TaskContract,
        auth: AuthorizationContext,
        *,
        now_epoch: Optional[int] = None,
    ) -> PlanDecision:
        now_epoch = int(time.time()) if now_epoch is None else int(now_epoch)
        manifests = self.registry.matching(task.operation)
        candidates = [self.evaluate_candidate(m, task, auth, now_epoch=now_epoch) for m in manifests]
        feasible = [c for c in candidates if c.feasible and c.resource_vector is not None]
        if not feasible:
            return PlanDecision(
                task_id=task.task_id,
                status="NO_FEASIBLE_ROUTE",
                selected_capability_id=None,
                selected_resource_vector=None,
                pareto_frontier=[],
                candidates=candidates,
                selection_order=task.selection_order,
                rationale=[
                    "No route survived authorization, quality, semantic-loss, privacy, irreversibility, energy, cost, and latency gates.",
                    "The planner did not weaken a hard constraint to produce a fluent answer.",
                ],
                permission_bypass_attempted=any(
                    "required_scopes_present" in c.rejection_reasons or "node_allowed" in c.rejection_reasons
                    for c in candidates
                ),
            )

        pairs = [(c.capability_id, c.resource_vector) for c in feasible if c.resource_vector is not None]
        frontier = pareto_frontier(pairs)
        frontier_evals = [c for c in feasible if c.capability_id in frontier]
        selected = min(
            frontier_evals,
            key=lambda c: c.resource_vector.objective_tuple(task.selection_order),  # type: ignore[union-attr]
        )
        return PlanDecision(
            task_id=task.task_id,
            status="ROUTE_SELECTED",
            selected_capability_id=selected.capability_id,
            selected_resource_vector=selected.resource_vector,
            pareto_frontier=frontier,
            candidates=candidates,
            selection_order=task.selection_order,
            rationale=[
                "Hard authorization and quality/risk constraints were applied before resource optimization.",
                "Non-dominated routes were retained on a Pareto frontier.",
                "The selected route minimizes the declared lexicographic order; physical energy is first by default.",
                "No permission, privacy, semantic-loss, or irreversibility deficit was traded away for lower energy.",
            ],
            permission_bypass_attempted=False,
            scalar_aggregate_used=False,
        )

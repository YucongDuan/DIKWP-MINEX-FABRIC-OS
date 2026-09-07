from __future__ import annotations

from typing import Any, Dict, List

from .models import PlanDecision, TaskContract


def build_semantic_graph(task: TaskContract, decision: PlanDecision) -> Dict[str, Any]:
    records: List[Dict[str, Any]] = []
    routes: List[Dict[str, Any]] = []

    def add(kind: str, record_id: str, content: Any, provenance: str) -> None:
        records.append({"record_id": record_id, "kind": kind, "content": content, "provenance": provenance})

    add("D", "D.task", {"task_id": task.task_id, "operation": task.operation, "inputs_present": sorted(task.inputs.keys())}, "task_contract")
    add(
        "D",
        "D.capabilities",
        [
            {
                "capability_id": c.capability_id,
                "mode": c.mode,
                "feasible": c.feasible,
                "resource_vector": c.resource_vector.as_dict() if c.resource_vector else None,
            }
            for c in decision.candidates
        ],
        "planner_observation",
    )
    add(
        "I",
        "I.route_differences",
        {
            "pareto_frontier": decision.pareto_frontier,
            "rejections": {c.capability_id: c.rejection_reasons for c in decision.candidates if c.rejection_reasons},
        },
        "candidate_comparison",
    )
    add(
        "K",
        "K.plan",
        {
            "status": decision.status,
            "selected_capability_id": decision.selected_capability_id,
            "selected_resource_vector": decision.selected_resource_vector.as_dict() if decision.selected_resource_vector else None,
        },
        "constraint_first_planning",
    )
    add(
        "W",
        "W.boundaries",
        {
            "constraints": task.constraints,
            "noncompensatory": ["authorization", "quality", "semantic_loss", "privacy", "irreversibility"],
            "scalar_aggregate_used": False,
        },
        "task_contract",
    )
    add(
        "P",
        "P.execution",
        {
            "purpose": task.purpose,
            "input": task.task_id,
            "output": decision.selected_capability_id,
            "automatic_external_action_authority": 0,
        },
        "executable_plan",
    )
    routes.extend(
        [
            {"source": "D.task", "target": "I.route_differences", "kind": "D->I", "content": "task requirements distinguish execution routes"},
            {"source": "D.capabilities", "target": "K.plan", "kind": "D->K", "content": "observed manifests support a bounded plan"},
            {"source": "W.boundaries", "target": "P.execution", "kind": "W->P", "content": "authorization and noncompensatory limits alter the executable route"},
            {"source": "K.plan", "target": "P.execution", "kind": "K->P", "content": "selected feasible plan becomes executable purpose"},
        ]
    )
    return {
        "protocol": "DIKWP multi-record, record-level routes, append-only lineage",
        "records": records,
        "routes": routes,
        "allowed_route_kinds": [f"{a}->{b}" for a in "DIKWP" for b in "DIKWP"],
        "translation_loss_required": True,
    }

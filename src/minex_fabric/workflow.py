from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .executors import execute_capability
from .io_utils import canonical_json, sha256_text, write_json
from .ledger import HashLedger
from .market import create_dry_run_settlement, create_quote
from .models import AuthorizationContext, CapabilityManifest, PlanDecision, TaskContract
from .planner import CapabilityPlanner
from .registry import CapabilityRegistry
from .semantic import build_semantic_graph


def run_task(
    task: TaskContract,
    registry: CapabilityRegistry,
    auth: AuthorizationContext,
    output_dir: str | Path,
    *,
    now_epoch: Optional[int] = None,
    execute: bool = True,
) -> Dict[str, Any]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    now_epoch = int(time.time()) if now_epoch is None else int(now_epoch)
    ledger = HashLedger()
    ledger.append("TASK_CONTRACT", task.as_dict())
    ledger.append("AUTHORIZATION_LEASE", auth.as_dict())
    planner = CapabilityPlanner(registry)
    decision = planner.plan(task, auth, now_epoch=now_epoch)
    ledger.append("PLAN_DECISION", decision.as_dict())
    execution_result: Dict[str, Any] | None = None
    settlement: Dict[str, Any] | None = None
    if execute and decision.selected_capability_id:
        manifest = registry.get(decision.selected_capability_id)
        execution_result = execute_capability(manifest, task)
        ledger.append("EXECUTION_RESULT", execution_result)
        if decision.selected_resource_vector and decision.selected_resource_vector.monetary_cost > 0:
            quote = create_quote(manifest, task, expires_at_epoch=now_epoch + 300)
            output_hash = sha256_text(canonical_json(execution_result["output"]))
            settlement = create_dry_run_settlement(quote, output_hash, execution_result["execution_state"] != "FAILED")
            ledger.append("MARKET_SETTLEMENT", settlement)
    semantic_graph = build_semantic_graph(task, decision)
    ledger.append("DIKWP_SEMANTIC_GRAPH", semantic_graph)
    residuals = []
    if decision.status != "ROUTE_SELECTED":
        residuals.append({"type": "NO_FEASIBLE_ROUTE", "next_action": "add an authorized capability or revise a declared constraint"})
    if any(c.resource_vector and c.resource_vector.evidence_class != "MEASURED" for c in decision.candidates):
        residuals.append({"type": "ENERGY_CALIBRATION_DEBT", "next_action": "measure energy on the actual hardware and update the manifest lineage"})
    if execution_result and execution_result.get("execution_state") == "DRY_RUN_ONLY":
        residuals.append({"type": "REAL_EXECUTION_NOT_PERFORMED", "next_action": "obtain named authority and execute through a verified adapter"})
    ledger.append("RESIDUAL_AND_CAUSAL_HANDOFF", {"residuals": residuals, "next_owner": task.requester})
    ledger.write(out / "evidence_ledger.jsonl")
    verification = HashLedger.verify_file(out / "evidence_ledger.jsonl")
    certificate = {
        "system": "DIKWP-MINEX-FABRIC-OS",
        "version": "1.0.0",
        "task_id": task.task_id,
        "status": decision.status,
        "selected_capability_id": decision.selected_capability_id,
        "selected_resource_vector": decision.selected_resource_vector.as_dict() if decision.selected_resource_vector else None,
        "permission_preserved": not decision.permission_bypass_attempted and decision.status == "ROUTE_SELECTED",
        "physical_energy_is_first_class": True,
        "non_energy_costs_not_silently_converted_to_joules": True,
        "scalar_aggregate_used": False,
        "automatic_external_action_authority": 0,
        "real_payment_performed": False,
        "execution_result": execution_result,
        "settlement": settlement,
        "residuals": residuals,
        "ledger_head_hash": verification["head_hash"],
        "ledger_valid": verification["valid"],
        "claim_boundary": "The certificate proves only the declared planner/executor run. It does not certify an external model, software vendor, energy meter, or market.",
    }
    write_json(out / "task_contract.json", task.as_dict())
    write_json(out / "authorization.json", auth.as_dict())
    write_json(out / "plan_decision.json", decision.as_dict())
    write_json(out / "execution_result.json", execution_result)
    write_json(out / "semantic_graph.json", semantic_graph)
    write_json(out / "residual_queue.json", residuals)
    write_json(out / "minex_certificate.json", certificate)
    write_json(out / "ledger_verification.json", verification)
    return certificate


def run_composite_task(
    task: TaskContract,
    registry: CapabilityRegistry,
    auth: AuthorizationContext,
    output_dir: str | Path,
    *,
    now_epoch: Optional[int] = None,
) -> Dict[str, Any]:
    from .energy import combine_vectors

    if not task.subtasks:
        return run_task(task, registry, auth, output_dir, now_epoch=now_epoch)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    decisions = []
    vectors = []
    certificates = []
    for index, raw in enumerate(task.subtasks):
        raw = dict(raw)
        raw.setdefault("task_id", f"{task.task_id}.step{index+1}")
        raw.setdefault("requester", task.requester)
        subtask = TaskContract.from_dict(raw)
        cert = run_task(subtask, registry, auth, out / subtask.task_id, now_epoch=now_epoch)
        certificates.append(cert)
        if cert.get("selected_resource_vector"):
            from .models import ResourceVector

            vectors.append(ResourceVector(**cert["selected_resource_vector"]))
    parallel = bool(task.constraints.get("parallel", False))
    combined = combine_vectors(vectors, parallel=parallel) if vectors else None
    summary = {
        "system": "DIKWP-MINEX-FABRIC-OS",
        "task_id": task.task_id,
        "composite": True,
        "parallel": parallel,
        "subtask_count": len(certificates),
        "subtask_certificates": certificates,
        "combined_resource_vector": combined.as_dict() if combined else None,
        "latency_composition": "critical_path_max" if parallel else "serial_sum",
        "automatic_external_action_authority": 0,
    }
    write_json(out / "composite_certificate.json", summary)
    return summary

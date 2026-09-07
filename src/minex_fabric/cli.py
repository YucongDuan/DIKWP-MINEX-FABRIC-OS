from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict

from . import SYSTEM_ID, __version__
from .authorization import issue_lease
from .calibration import calibrate_manifest
from .federation import serve_node
from .internalizer import internalize_file
from .io_utils import read_json, write_json
from .ledger import HashLedger
from .models import AuthorizationContext, CapabilityManifest, TaskContract
from .registry import CapabilityRegistry
from .workflow import run_composite_task, run_task


def _default_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent.parent.parent, Path.cwd()]:
        if (candidate / "examples" / "capabilities").exists():
            return candidate
    return Path.cwd()


def _load_auth(path: str | None) -> AuthorizationContext:
    if path:
        return AuthorizationContext.from_dict(read_json(path))
    return AuthorizationContext(
        principal="local-demo-owner",
        scopes=["*"],
        allowed_nodes=["*"],
        allowed_data_classes=["*"],
        expires_at_epoch=4_102_444_800,
        max_calls=1000,
        allow_paid=True,
        max_payment=100.0,
        lease_id="demo-lease",
    )


def cmd_inspect(args: argparse.Namespace) -> int:
    print(
        json.dumps(
            {
                "system": SYSTEM_ID,
                "version": __version__,
                "purpose": "route a declared purpose to an authorized capability with minimum physical energy and minimum effective expenditure",
                "execution_modes": ["MODEL_NATIVE", "GENERATED_CODE", "LOCAL_API", "REMOTE_API", "BROWSER", "GUI", "FEDERATED_NODE", "HUMAN"],
                "hard_gates": ["authorization", "data_class", "quality", "reliability", "semantic_loss", "privacy", "irreversibility", "budget", "deadline"],
                "selection": "Pareto frontier plus declared lexicographic order; physical energy first by default",
                "automatic_external_action_authority": 0,
                "real_payment_adapter": "not included",
                "arbitrary_shell_execution": "prohibited",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_plan_or_run(args: argparse.Namespace, *, execute: bool) -> int:
    registry = CapabilityRegistry.from_directory(args.capabilities)
    task = TaskContract.from_dict(read_json(args.task))
    auth = _load_auth(args.auth)
    if task.subtasks:
        result = run_composite_task(task, registry, auth, args.output, now_epoch=args.now)
    else:
        result = run_task(task, registry, auth, args.output, now_epoch=args.now, execute=execute)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status", "ROUTE_SELECTED") != "NO_FEASIBLE_ROUTE" else 2


def cmd_internalize(args: argparse.Namespace) -> int:
    result = internalize_file(args.recipe, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "INTERNALIZED_WITHIN_TEST_SCOPE" else 2


def cmd_verify(args: argparse.Namespace) -> int:
    result = HashLedger.verify_file(args.ledger)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 3


def cmd_issue_lease(args: argparse.Namespace) -> int:
    payload = read_json(args.payload)
    print(issue_lease(payload, args.secret))
    return 0


def cmd_calibrate(args: argparse.Namespace) -> int:
    manifest = CapabilityManifest.from_dict(read_json(args.manifest))
    updated = calibrate_manifest(manifest, read_json(args.outcome), alpha=args.alpha)
    write_json(args.output, updated.as_dict())
    print(json.dumps(updated.as_dict(), ensure_ascii=False, indent=2))
    return 0


def cmd_suite(args: argparse.Namespace) -> int:
    root = Path(args.root)
    registry = CapabilityRegistry.from_directory(root / "examples" / "capabilities")
    auth = _load_auth(None)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    summaries = []
    for task_path in sorted((root / "examples" / "tasks").glob("*.json")):
        raw = read_json(task_path)
        task_auth = AuthorizationContext.from_dict(raw.pop("_authorization")) if "_authorization" in raw else auth
        task = TaskContract.from_dict(raw)
        result = (
            run_composite_task(task, registry, task_auth, out / task.task_id, now_epoch=args.now)
            if task.subtasks
            else run_task(task, registry, task_auth, out / task.task_id, now_epoch=args.now, execute=True)
        )
        summaries.append({"task": task.task_id, "status": result.get("status", "COMPOSITE"), "selected": result.get("selected_capability_id")})
    write_json(out / "suite_summary.json", {"tasks": summaries, "count": len(summaries)})
    print(json.dumps({"count": len(summaries), "tasks": summaries}, ensure_ascii=False, indent=2))
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    registry = CapabilityRegistry.from_directory(args.capabilities)
    serve_node(
        registry,
        node_id=args.node_id,
        host=args.host,
        port=args.port,
        bearer_token=args.bearer_token,
        lease_secret=args.lease_secret,
        allow_execution=args.allow_execution,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="minex-fabric", description="DIKWP-MINEX-FABRIC-OS")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("inspect")
    p.set_defaults(func=cmd_inspect)

    for name, execute in (("plan", False), ("run", True)):
        p = sub.add_parser(name)
        p.add_argument("task")
        p.add_argument("--capabilities", required=True)
        p.add_argument("--auth")
        p.add_argument("--output", required=True)
        p.add_argument("--now", type=int, default=1_800_000_000)
        p.set_defaults(func=lambda a, execute=execute: cmd_plan_or_run(a, execute=execute))

    p = sub.add_parser("suite")
    p.add_argument("--root", default=str(_default_root()))
    p.add_argument("--output", required=True)
    p.add_argument("--now", type=int, default=1_800_000_000)
    p.set_defaults(func=cmd_suite)

    p = sub.add_parser("internalize")
    p.add_argument("recipe")
    p.add_argument("--output", required=True)
    p.set_defaults(func=cmd_internalize)

    p = sub.add_parser("verify")
    p.add_argument("ledger")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("issue-lease")
    p.add_argument("payload")
    p.add_argument("--secret", required=True)
    p.set_defaults(func=cmd_issue_lease)

    p = sub.add_parser("calibrate")
    p.add_argument("manifest")
    p.add_argument("outcome")
    p.add_argument("--alpha", type=float, default=0.3)
    p.add_argument("--output", required=True)
    p.set_defaults(func=cmd_calibrate)

    p = sub.add_parser("serve-node")
    p.add_argument("--capabilities", required=True)
    p.add_argument("--node-id", default="node-local")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--bearer-token", default=os.environ.get("MINEX_BEARER_TOKEN", ""))
    p.add_argument("--lease-secret", default=os.environ.get("MINEX_LEASE_SECRET", ""))
    p.add_argument("--allow-execution", action="store_true")
    p.set_defaults(func=cmd_serve)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

from .executors import safe_eval
from .io_utils import read_json, write_json
from .models import CapabilityManifest


class InternalizationError(RuntimeError):
    pass


def internalize_recipe(recipe: Dict[str, Any]) -> Dict[str, Any]:
    """Compile a licensed, declarative function recipe into a local capability.

    This does not copy proprietary model weights, bypass a license, or infer a
    secret API. It accepts only a caller-supplied expression/pipeline and
    explicit conformance tests.
    """
    if not recipe.get("license_permission_confirmed", False):
        raise InternalizationError("license permission not confirmed")
    expression = str(recipe["expression"])
    input_var = str(recipe.get("input_var", "x"))
    tests = list(recipe.get("tests", []))
    if not tests:
        raise InternalizationError("at least one conformance test is required")
    results: List[Dict[str, Any]] = []
    passed = True
    tolerance = float(recipe.get("tolerance", 1e-9))
    for i, test in enumerate(tests):
        variables = {str(k): float(v) for k, v in dict(test.get("variables", {})).items()}
        if input_var in test:
            variables[input_var] = float(test[input_var])
        actual = safe_eval(expression, variables)
        expected = float(test["expected"])
        ok = abs(actual - expected) <= tolerance
        passed = passed and ok
        results.append({"index": i, "variables": variables, "expected": expected, "actual": actual, "passed": ok})
    if not passed:
        return {"status": "CONFORMANCE_FAILED", "tests": results, "manifest": None}

    manifest = CapabilityManifest(
        capability_id=str(recipe["capability_id"]),
        name=str(recipe.get("name", recipe["capability_id"])),
        operation=str(recipe["operation"]),
        mode="GENERATED_CODE",
        provider_id=str(recipe.get("provider_id", "local-owner")),
        node_id=str(recipe.get("node_id", "local")),
        version=str(recipe.get("version", "1.0.0")),
        description=str(recipe.get("description", "Conformance-tested declarative local function")),
        required_scopes=list(recipe.get("required_scopes", [])),
        allowed_data_classes=list(recipe.get("allowed_data_classes", ["PUBLIC", "INTERNAL", "SENSITIVE"])),
        base_energy_j=float(recipe.get("base_energy_j", 1.0)),
        energy_per_work_unit_j=float(recipe.get("energy_per_work_unit_j", 0.01)),
        base_latency_ms=float(recipe.get("base_latency_ms", 1.0)),
        expected_quality=float(recipe.get("expected_quality", 0.999)),
        reliability=float(recipe.get("reliability", 0.999)),
        semantic_loss=float(recipe.get("semantic_loss", 0.0)),
        privacy_risk=float(recipe.get("privacy_risk", 0.01)),
        irreversibility=0.0,
        internalizable=False,
        license=str(recipe.get("license", "CALLER-DECLARED")),
        executor="builtin" if recipe.get("builtin_operation", False) else "dry_run",
        tags=["internalized", "conformance-tested"],
        lineage={
            "source_capability_id": recipe.get("source_capability_id"),
            "recipe_type": "SAFE_EXPRESSION",
            "expression": expression,
            "conformance_test_count": len(tests),
            "license_permission_confirmed": True,
        },
    )
    return {"status": "INTERNALIZED_WITHIN_TEST_SCOPE", "tests": results, "manifest": manifest.as_dict()}


def internalize_file(recipe_path: str | Path, output_path: str | Path) -> Dict[str, Any]:
    result = internalize_recipe(read_json(recipe_path))
    write_json(output_path, result)
    return result

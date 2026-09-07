from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import math
import re
import statistics
import time
from collections import Counter
from typing import Any, Callable, Dict

from .models import CapabilityManifest, TaskContract


class ExecutionError(RuntimeError):
    pass


_ALLOWED_AST = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Constant,
    ast.Name,
    ast.Load,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
    ast.USub,
    ast.UAdd,
    ast.Call,
)
_ALLOWED_FUNCTIONS = {"abs": abs, "round": round, "min": min, "max": max, "sqrt": math.sqrt}


def safe_eval(expression: str, variables: Dict[str, float]) -> float:
    tree = ast.parse(expression, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_AST):
            raise ExecutionError(f"unsafe expression node: {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id not in variables and node.id not in _ALLOWED_FUNCTIONS:
            raise ExecutionError(f"unknown variable: {node.id}")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in _ALLOWED_FUNCTIONS:
                raise ExecutionError("function is not allowlisted")
    return float(eval(compile(tree, "<safe-expression>", "eval"), {"__builtins__": {}}, {**_ALLOWED_FUNCTIONS, **variables}))


def op_text_normalize(inputs: Dict[str, Any]) -> Dict[str, Any]:
    text = str(inputs.get("text", ""))
    normalized = re.sub(r"\s+", " ", text).strip()
    return {"text": normalized, "characters": len(normalized), "words": len(normalized.split())}


def op_text_summarize(inputs: Dict[str, Any]) -> Dict[str, Any]:
    text = str(inputs.get("text", ""))
    limit = int(inputs.get("sentences", 3))
    sentences = [s.strip() for s in re.split(r"(?<=[.!?。！？])\s+", text) if s.strip()]
    if len(sentences) <= limit:
        selected = sentences
    else:
        words = re.findall(r"[A-Za-z0-9_\u4e00-\u9fff]+", text.lower())
        freq = Counter(w for w in words if len(w) > 1)
        scored = []
        for idx, sentence in enumerate(sentences):
            sw = re.findall(r"[A-Za-z0-9_\u4e00-\u9fff]+", sentence.lower())
            score = sum(freq[w] for w in sw) / max(1, len(sw))
            scored.append((score, idx, sentence))
        chosen = sorted(sorted(scored, reverse=True)[:limit], key=lambda x: x[1])
        selected = [x[2] for x in chosen]
    return {"summary": " ".join(selected), "source_sentence_count": len(sentences), "selected_sentence_count": len(selected)}


def _load_csv_text(inputs: Dict[str, Any]) -> str:
    if "csv_text" in inputs:
        return str(inputs["csv_text"])
    if "path" in inputs:
        with open(str(inputs["path"]), "r", encoding="utf-8-sig", newline="") as f:
            return f.read()
    raise ExecutionError("csv.profile requires csv_text or path")


def op_csv_profile(inputs: Dict[str, Any]) -> Dict[str, Any]:
    text = _load_csv_text(inputs)
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    columns = reader.fieldnames or []
    profile: Dict[str, Any] = {"rows": len(rows), "columns": columns, "column_profiles": {}}
    for col in columns:
        values = [r.get(col, "") for r in rows]
        nonempty = [v for v in values if v not in (None, "")]
        numeric = []
        for value in nonempty:
            try:
                numeric.append(float(value))
            except (TypeError, ValueError):
                pass
        cp: Dict[str, Any] = {
            "nonempty": len(nonempty),
            "missing": len(values) - len(nonempty),
            "unique": len(set(nonempty)),
        }
        if numeric and len(numeric) == len(nonempty):
            cp.update(
                {
                    "type": "numeric",
                    "min": min(numeric),
                    "max": max(numeric),
                    "mean": statistics.fmean(numeric),
                }
            )
        else:
            cp.update({"type": "text", "top_values": Counter(nonempty).most_common(5)})
        profile["column_profiles"][col] = cp
    return profile


def op_math_evaluate(inputs: Dict[str, Any]) -> Dict[str, Any]:
    expression = str(inputs.get("expression", ""))
    variables = {str(k): float(v) for k, v in dict(inputs.get("variables", {})).items()}
    return {"expression": expression, "result": safe_eval(expression, variables)}


def op_temperature_convert(inputs: Dict[str, Any]) -> Dict[str, Any]:
    value = float(inputs["value"])
    src = str(inputs.get("from", "C")).upper()
    dst = str(inputs.get("to", "F")).upper()
    if src == dst:
        result = value
    else:
        if src == "C":
            c = value
        elif src == "F":
            c = (value - 32) * 5 / 9
        elif src == "K":
            c = value - 273.15
        else:
            raise ExecutionError("unsupported source unit")
        if dst == "C":
            result = c
        elif dst == "F":
            result = c * 9 / 5 + 32
        elif dst == "K":
            result = c + 273.15
        else:
            raise ExecutionError("unsupported target unit")
    return {"value": value, "from": src, "to": dst, "result": round(result, 10)}


def op_hash(inputs: Dict[str, Any]) -> Dict[str, Any]:
    data = inputs.get("data", "")
    if not isinstance(data, (str, bytes)):
        data = json.dumps(data, ensure_ascii=False, sort_keys=True)
    b = data if isinstance(data, bytes) else data.encode("utf-8")
    return {"sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)}


def op_json_select(inputs: Dict[str, Any]) -> Dict[str, Any]:
    obj = dict(inputs.get("object", {}))
    keys = [str(k) for k in inputs.get("keys", [])]
    return {"object": {k: obj.get(k) for k in keys}}


def op_report_compose(inputs: Dict[str, Any]) -> Dict[str, Any]:
    title = str(inputs.get("title", "Report"))
    sections = list(inputs.get("sections", []))
    lines = [f"# {title}", ""]
    for section in sections:
        lines.extend([f"## {section.get('heading','Section')}", "", str(section.get("body", "")), ""])
    return {"markdown": "\n".join(lines).rstrip() + "\n", "section_count": len(sections)}


_BUILTINS: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
    "text.normalize": op_text_normalize,
    "text.summarize.extractive": op_text_summarize,
    "csv.profile": op_csv_profile,
    "math.evaluate": op_math_evaluate,
    "unit.convert.temperature": op_temperature_convert,
    "data.hash.sha256": op_hash,
    "json.select": op_json_select,
    "report.compose.markdown": op_report_compose,
}


def execute_builtin(operation: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    if operation not in _BUILTINS:
        raise ExecutionError(f"no allowlisted builtin for operation: {operation}")
    return _BUILTINS[operation](inputs)


def execute_capability(manifest: CapabilityManifest, task: TaskContract, *, allow_external: bool = False) -> Dict[str, Any]:
    started = time.perf_counter()
    if manifest.executor == "builtin":
        output = execute_builtin(manifest.operation, task.inputs)
        state = "EXECUTED_LOCALLY"
    elif manifest.executor == "dry_run":
        output = {
            "planned_operation": manifest.operation,
            "mode": manifest.mode,
            "endpoint": manifest.endpoint,
            "message": "External execution was not performed. This is a dry-run plan.",
        }
        state = "DRY_RUN_ONLY"
    else:
        raise ExecutionError(f"unknown executor: {manifest.executor}")
    elapsed_ms = (time.perf_counter() - started) * 1000
    return {
        "execution_state": state,
        "capability_id": manifest.capability_id,
        "mode": manifest.mode,
        "operation": manifest.operation,
        "output": output,
        "measured_wall_time_ms": round(elapsed_ms, 6),
        "external_action_performed": False,
    }

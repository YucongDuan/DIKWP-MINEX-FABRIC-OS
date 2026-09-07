from __future__ import annotations

from dataclasses import replace
from typing import Any, Dict

from .models import CapabilityManifest


def calibrate_manifest(manifest: CapabilityManifest, outcome: Dict[str, Any], *, alpha: float = 0.3) -> CapabilityManifest:
    if not 0.0 < alpha <= 1.0:
        raise ValueError("alpha must be in (0,1]")
    energy = float(outcome.get("measured_energy_j", manifest.base_energy_j))
    latency = float(outcome.get("measured_latency_ms", manifest.base_latency_ms))
    quality = float(outcome.get("measured_quality", manifest.expected_quality))
    success = bool(outcome.get("success", True))
    reliability_observation = 1.0 if success else 0.0
    lineage = dict(manifest.lineage)
    lineage.setdefault("calibration_history", []).append(
        {
            "prior_version": manifest.version,
            "measured_energy_j": energy,
            "measured_latency_ms": latency,
            "measured_quality": quality,
            "success": success,
        }
    )
    return replace(
        manifest,
        version=str(outcome.get("new_version", manifest.version + "+calibrated")),
        base_energy_j=(1 - alpha) * manifest.base_energy_j + alpha * energy,
        base_latency_ms=(1 - alpha) * manifest.base_latency_ms + alpha * latency,
        expected_quality=max(0.0, min(1.0, (1 - alpha) * manifest.expected_quality + alpha * quality)),
        reliability=max(0.0, min(1.0, (1 - alpha) * manifest.reliability + alpha * reliability_observation)),
        lineage=lineage,
    )

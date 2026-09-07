from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

from .io_utils import read_json
from .models import CapabilityManifest


class CapabilityRegistry:
    def __init__(self, manifests: Iterable[CapabilityManifest] = ()) -> None:
        self._items: Dict[str, CapabilityManifest] = {}
        for manifest in manifests:
            self.register(manifest)

    def register(self, manifest: CapabilityManifest, *, replace: bool = False) -> None:
        if manifest.capability_id in self._items and not replace:
            raise ValueError(f"capability already registered: {manifest.capability_id}")
        self._items[manifest.capability_id] = manifest

    def get(self, capability_id: str) -> CapabilityManifest:
        return self._items[capability_id]

    def all(self) -> List[CapabilityManifest]:
        return sorted(self._items.values(), key=lambda x: x.capability_id)

    def matching(self, operation: str) -> List[CapabilityManifest]:
        return [m for m in self.all() if m.enabled and m.operation == operation]

    @classmethod
    def from_directory(cls, directory: str | Path) -> "CapabilityRegistry":
        manifests: List[CapabilityManifest] = []
        for path in sorted(Path(directory).glob("*.json")):
            value = read_json(path)
            if isinstance(value, list):
                manifests.extend(CapabilityManifest.from_dict(x) for x in value)
            else:
                manifests.append(CapabilityManifest.from_dict(value))
        return cls(manifests)

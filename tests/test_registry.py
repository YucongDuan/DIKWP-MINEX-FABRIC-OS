import json
import tempfile
import unittest
from pathlib import Path

from minex_fabric.models import CapabilityManifest
from minex_fabric.registry import CapabilityRegistry


class RegistryTests(unittest.TestCase):
    def manifest(self,cid="a",op="op"):
        return CapabilityManifest(cid,cid,op,"LOCAL_API","p","n","1")

    def test_register_get(self):
        r=CapabilityRegistry(); r.register(self.manifest())
        self.assertEqual(r.get("a").name,"a")

    def test_duplicate_rejected(self):
        r=CapabilityRegistry([self.manifest()])
        with self.assertRaises(ValueError): r.register(self.manifest())

    def test_replace(self):
        r=CapabilityRegistry([self.manifest()]); r.register(self.manifest(),replace=True)
        self.assertEqual(len(r.all()),1)

    def test_matching(self):
        r=CapabilityRegistry([self.manifest("a","x"),self.manifest("b","y")])
        self.assertEqual([m.capability_id for m in r.matching("x")],["a"])

    def test_directory_load(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"a.json"; p.write_text(json.dumps(self.manifest().as_dict()))
            r=CapabilityRegistry.from_directory(d)
            self.assertEqual(len(r.all()),1)


if __name__ == "__main__":
    unittest.main()

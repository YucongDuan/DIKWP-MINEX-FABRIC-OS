import tempfile
import unittest
from pathlib import Path

from minex_fabric.internalizer import InternalizationError, internalize_recipe
from minex_fabric.io_utils import write_json
from minex_fabric.ledger import HashLedger
from minex_fabric.market import create_dry_run_settlement, create_quote
from minex_fabric.models import CapabilityManifest, TaskContract


class LedgerMarketInternalizerTests(unittest.TestCase):
    def test_ledger_valid(self):
        l=HashLedger(); l.append("A",{"x":1}); l.append("B",{"y":2})
        self.assertTrue(HashLedger.verify_rows([e.as_dict() for e in l.events])["valid"])

    def test_ledger_tamper_detected(self):
        l=HashLedger(); l.append("A",{"x":1})
        rows=[e.as_dict() for e in l.events]; rows[0]["payload"]["x"]=2
        self.assertFalse(HashLedger.verify_rows(rows)["valid"])

    def test_ledger_file(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"l.jsonl"; l=HashLedger(); l.append("A",{}); l.write(p)
            self.assertTrue(HashLedger.verify_file(p)["valid"])

    def test_quote(self):
        m=CapabilityManifest("c","c","op","REMOTE_API","p","n","1",monetary_cost_base=.2)
        q=create_quote(m,TaskContract("t","p","op"),expires_at_epoch=100)
        self.assertEqual(q.price,.2)
        self.assertTrue(q.quote_id.startswith("quote-"))

    def test_dry_run_settlement(self):
        m=CapabilityManifest("c","c","op","REMOTE_API","p","n","1",monetary_cost_base=.2)
        q=create_quote(m,TaskContract("t","p","op"),expires_at_epoch=100)
        s=create_dry_run_settlement(q,"abc",True)
        self.assertFalse(s["real_funds_moved"])
        self.assertEqual(s["payment_state"],"DRY_RUN_SETTLED")

    def recipe(self):
        return {"capability_id":"x","operation":"op","expression":"x*2","input_var":"x","license_permission_confirmed":True,"tests":[{"x":1,"expected":2},{"x":2,"expected":4}]}

    def test_internalization_passes(self):
        r=internalize_recipe(self.recipe())
        self.assertEqual(r["status"],"INTERNALIZED_WITHIN_TEST_SCOPE")
        self.assertEqual(r["manifest"]["mode"],"GENERATED_CODE")

    def test_internalization_fails_test(self):
        r=self.recipe(); r["tests"][0]["expected"]=3
        result=internalize_recipe(r)
        self.assertEqual(result["status"],"CONFORMANCE_FAILED")

    def test_internalization_requires_license(self):
        r=self.recipe(); r["license_permission_confirmed"]=False
        with self.assertRaises(InternalizationError):
            internalize_recipe(r)

    def test_internalization_requires_tests(self):
        r=self.recipe(); r["tests"]=[]
        with self.assertRaises(InternalizationError):
            internalize_recipe(r)


if __name__ == "__main__":
    unittest.main()

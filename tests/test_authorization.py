import time
import unittest

from minex_fabric.authorization import check_authorization, issue_lease, verify_lease
from minex_fabric.models import AuthorizationContext, CapabilityManifest, TaskContract


class AuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.m = CapabilityManifest(
            "cap", "Cap", "op", "LOCAL_API", "p", "node", "1",
            required_scopes=["read"], allowed_data_classes=["PUBLIC"]
        )
        self.t = TaskContract("t", "purpose", "op", input_data_class="PUBLIC")

    def auth(self, **overrides):
        d = dict(principal="u", scopes=["read"], allowed_nodes=["node"], allowed_data_classes=["PUBLIC"], expires_at_epoch=2000, max_calls=2, allow_paid=False, max_payment=0, lease_id="l")
        d.update(overrides)
        return AuthorizationContext(**d)

    def test_authorized(self):
        ok, reasons, _ = check_authorization(self.m, self.t, self.auth(), now_epoch=1000)
        self.assertTrue(ok)
        self.assertEqual(reasons, [])

    def test_expired_rejected(self):
        ok, reasons, _ = check_authorization(self.m, self.t, self.auth(expires_at_epoch=10), now_epoch=1000)
        self.assertFalse(ok)
        self.assertIn("lease_not_expired", reasons)

    def test_scope_rejected(self):
        ok, reasons, _ = check_authorization(self.m, self.t, self.auth(scopes=[]), now_epoch=1000)
        self.assertFalse(ok)
        self.assertIn("required_scopes_present", reasons)

    def test_node_rejected(self):
        ok, reasons, _ = check_authorization(self.m, self.t, self.auth(allowed_nodes=["other"]), now_epoch=1000)
        self.assertFalse(ok)
        self.assertIn("node_allowed", reasons)

    def test_data_class_rejected(self):
        t = TaskContract("t", "p", "op", input_data_class="SENSITIVE")
        ok, reasons, _ = check_authorization(self.m, t, self.auth(allowed_data_classes=["SENSITIVE"]), now_epoch=1000)
        self.assertFalse(ok)
        self.assertIn("data_class_allowed_by_capability", reasons)

    def test_paid_route_requires_permission(self):
        m = CapabilityManifest("cap", "Cap", "op", "REMOTE_API", "p", "node", "1", monetary_cost_base=1)
        ok, reasons, _ = check_authorization(m, self.t, self.auth(scopes=["*"], allow_paid=False), now_epoch=1000)
        self.assertFalse(ok)
        self.assertIn("paid_route_authorized", reasons)

    def test_lease_issue_verify(self):
        token = issue_lease({"lease_id":"x","expires_at_epoch":2000}, "secret")
        self.assertEqual(verify_lease(token, "secret", now_epoch=1000)["lease_id"], "x")

    def test_lease_bad_signature(self):
        token = issue_lease({"lease_id":"x","expires_at_epoch":2000}, "secret")
        with self.assertRaises(ValueError):
            verify_lease(token, "wrong", now_epoch=1000)

    def test_lease_expired(self):
        token = issue_lease({"lease_id":"x","expires_at_epoch":10}, "secret")
        with self.assertRaises(ValueError):
            verify_lease(token, "secret", now_epoch=1000)


if __name__ == "__main__":
    unittest.main()

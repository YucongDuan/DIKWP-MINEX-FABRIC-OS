import unittest

from minex_fabric.models import AuthorizationContext, CapabilityManifest, ResourceVector, TaskContract


class ModelTests(unittest.TestCase):
    def test_manifest_accepts_known_mode(self):
        m = CapabilityManifest("x", "x", "op", "MODEL_NATIVE", "p", "n", "1")
        self.assertEqual(m.mode, "MODEL_NATIVE")

    def test_manifest_rejects_unknown_mode(self):
        with self.assertRaises(ValueError):
            CapabilityManifest("x", "x", "op", "BAD", "p", "n", "1")

    def test_manifest_rejects_probability_out_of_range(self):
        with self.assertRaises(ValueError):
            CapabilityManifest("x", "x", "op", "LOCAL_API", "p", "n", "1", expected_quality=1.2)

    def test_task_roundtrip(self):
        task = TaskContract("t", "p", "op", inputs={"x": 1})
        self.assertEqual(TaskContract.from_dict(task.as_dict()).inputs["x"], 1)

    def test_auth_roundtrip(self):
        a = AuthorizationContext("p", ["x"], ["n"], ["PUBLIC"], 99)
        self.assertEqual(AuthorizationContext.from_dict(a.as_dict()).principal, "p")

    def test_resource_objective_order(self):
        v = ResourceVector(1, 2, 3, 4, 5, .1, .2, .3, .9, .8)
        self.assertEqual(v.objective_tuple(["physical_energy_j", "latency_ms"]), (1, 3))

    def test_default_selection_starts_with_energy(self):
        t = TaskContract("t", "p", "op")
        self.assertEqual(t.selection_order[0], "physical_energy_j")


if __name__ == "__main__":
    unittest.main()

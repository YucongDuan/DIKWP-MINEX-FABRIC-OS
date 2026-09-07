import unittest

from minex_fabric.energy import combine_vectors, dominates, estimate_resources, pareto_frontier
from minex_fabric.models import CapabilityManifest, ResourceVector, TaskContract


class EnergyTests(unittest.TestCase):
    def test_local_estimate(self):
        m = CapabilityManifest("c","c","op","LOCAL_API","p","n","1",base_energy_j=2,energy_per_work_unit_j=.5)
        v = estimate_resources(m, TaskContract("t","p","op",work_units=4,input_bytes=1_000_000))
        self.assertEqual(v.physical_energy_j, 4)
        self.assertEqual(v.data_egress_bytes, 0)

    def test_remote_network_energy(self):
        m = CapabilityManifest("c","c","op","REMOTE_API","p","n","1",base_energy_j=2,network_energy_per_mb_j=3)
        v = estimate_resources(m, TaskContract("t","p","op",input_bytes=2_000_000))
        self.assertEqual(v.physical_energy_j, 8)
        self.assertEqual(v.data_egress_bytes, 2_000_000)

    def test_dominates(self):
        a = ResourceVector(1,1,1,1,1,.1,.1,.1,.9,.9)
        b = ResourceVector(2,2,2,2,2,.2,.2,.2,.8,.8)
        self.assertTrue(dominates(a,b))

    def test_not_dominates_tradeoff(self):
        a = ResourceVector(1,2,1,1,1,.1,.1,.1,.9,.9)
        b = ResourceVector(2,1,1,1,1,.1,.1,.1,.9,.9)
        self.assertFalse(dominates(a,b))

    def test_pareto_frontier(self):
        a = ResourceVector(1,1,1,1,1,.1,.1,.1,.9,.9)
        b = ResourceVector(2,2,2,2,2,.2,.2,.2,.8,.8)
        self.assertEqual(pareto_frontier([("a",a),("b",b)]), ["a"])

    def test_combine_serial_latency(self):
        a = ResourceVector(1,1,2,1,1,.1,.1,.1,.9,.9)
        b = ResourceVector(1,1,3,1,1,.2,.2,.2,.8,.8)
        c = combine_vectors([a,b],parallel=False)
        self.assertEqual(c.latency_ms,5)
        self.assertEqual(c.physical_energy_j,2)

    def test_combine_parallel_latency(self):
        a = ResourceVector(1,1,2,1,1,.1,.1,.1,.9,.9)
        b = ResourceVector(1,1,3,1,1,.2,.2,.2,.8,.8)
        c = combine_vectors([a,b],parallel=True)
        self.assertEqual(c.latency_ms,3)
        self.assertEqual(c.expected_quality,.8)


if __name__ == "__main__":
    unittest.main()

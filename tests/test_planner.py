import unittest

from minex_fabric.models import AuthorizationContext, CapabilityManifest, TaskContract
from minex_fabric.planner import CapabilityPlanner
from minex_fabric.registry import CapabilityRegistry


class PlannerTests(unittest.TestCase):
    def auth(self, scopes=None, paid=True):
        return AuthorizationContext("u",scopes or ["*"],["*"],["*"],2000,allow_paid=paid,max_payment=10)

    def manifest(self, cid, energy, *, quality=.99, mode="LOCAL_API", scopes=None, privacy=.1, cost=0):
        return CapabilityManifest(cid,cid,"op",mode,"p","n","1",required_scopes=scopes or [],base_energy_j=energy,expected_quality=quality,reliability=.99,privacy_risk=privacy,monetary_cost_base=cost)

    def test_selects_lowest_energy_after_gates(self):
        reg=CapabilityRegistry([self.manifest("a",10),self.manifest("b",2)])
        d=CapabilityPlanner(reg).plan(TaskContract("t","p","op",constraints={"min_quality":.9}),self.auth(),now_epoch=1000)
        self.assertEqual(d.selected_capability_id,"b")

    def test_quality_gate_precedes_energy(self):
        reg=CapabilityRegistry([self.manifest("cheap",1,quality=.5),self.manifest("good",10,quality=.99)])
        d=CapabilityPlanner(reg).plan(TaskContract("t","p","op",constraints={"min_quality":.9}),self.auth(),now_epoch=1000)
        self.assertEqual(d.selected_capability_id,"good")

    def test_privacy_gate(self):
        reg=CapabilityRegistry([self.manifest("bad",1,privacy=.9),self.manifest("good",10,privacy=.1)])
        d=CapabilityPlanner(reg).plan(TaskContract("t","p","op",constraints={"max_privacy_risk":.2}),self.auth(),now_epoch=1000)
        self.assertEqual(d.selected_capability_id,"good")

    def test_scope_gate(self):
        reg=CapabilityRegistry([self.manifest("gui",1,mode="GUI",scopes=["gui"]),self.manifest("local",5)])
        d=CapabilityPlanner(reg).plan(TaskContract("t","p","op"),self.auth(scopes=["read"]),now_epoch=1000)
        self.assertEqual(d.selected_capability_id,"local")

    def test_no_feasible_route(self):
        reg=CapabilityRegistry([self.manifest("a",1,quality=.2)])
        d=CapabilityPlanner(reg).plan(TaskContract("t","p","op",constraints={"min_quality":.9}),self.auth(),now_epoch=1000)
        self.assertEqual(d.status,"NO_FEASIBLE_ROUTE")

    def test_cost_gate(self):
        reg=CapabilityRegistry([self.manifest("paid",1,cost=5),self.manifest("free",10,cost=0)])
        d=CapabilityPlanner(reg).plan(TaskContract("t","p","op",constraints={"max_cost":1}),self.auth(),now_epoch=1000)
        self.assertEqual(d.selected_capability_id,"free")

    def test_local_requirement(self):
        reg=CapabilityRegistry([self.manifest("remote",1,mode="REMOTE_API"),self.manifest("local",5)])
        d=CapabilityPlanner(reg).plan(TaskContract("t","p","op",constraints={"require_local":True}),self.auth(),now_epoch=1000)
        self.assertEqual(d.selected_capability_id,"local")

    def test_allowed_modes(self):
        reg=CapabilityRegistry([self.manifest("api",1,mode="LOCAL_API"),self.manifest("model",5,mode="MODEL_NATIVE")])
        d=CapabilityPlanner(reg).plan(TaskContract("t","p","op",constraints={"allowed_modes":["MODEL_NATIVE"]}),self.auth(),now_epoch=1000)
        self.assertEqual(d.selected_capability_id,"model")

    def test_scalar_aggregate_never_used(self):
        reg=CapabilityRegistry([self.manifest("a",1)])
        d=CapabilityPlanner(reg).plan(TaskContract("t","p","op"),self.auth(),now_epoch=1000)
        self.assertFalse(d.scalar_aggregate_used)

    def test_frontier_keeps_tradeoff(self):
        a=self.manifest("a",1,cost=2)
        b=self.manifest("b",2,cost=1)
        reg=CapabilityRegistry([a,b])
        d=CapabilityPlanner(reg).plan(TaskContract("t","p","op"),self.auth(),now_epoch=1000)
        self.assertEqual(set(d.pareto_frontier),{"a","b"})


if __name__ == "__main__":
    unittest.main()

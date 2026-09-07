import json
import tempfile
import unittest
from pathlib import Path

from minex_fabric.calibration import calibrate_manifest
from minex_fabric.io_utils import read_json
from minex_fabric.models import AuthorizationContext, CapabilityManifest, TaskContract
from minex_fabric.registry import CapabilityRegistry
from minex_fabric.semantic import build_semantic_graph
from minex_fabric.planner import CapabilityPlanner
from minex_fabric.workflow import run_composite_task, run_task


class CalibrationSemanticWorkflowTests(unittest.TestCase):
    def auth(self):
        return AuthorizationContext("u",["*"],["*"],["*"],2000,allow_paid=True,max_payment=100)

    def manifest(self, cid="c", op="data.hash.sha256", energy=1):
        return CapabilityManifest(cid,cid,op,"LOCAL_API","p","local","1",base_energy_j=energy,executor="builtin")

    def test_calibration_updates_energy(self):
        m=self.manifest(energy=10)
        u=calibrate_manifest(m,{"measured_energy_j":4,"measured_latency_ms":2,"measured_quality":1,"success":True},alpha=.5)
        self.assertEqual(u.base_energy_j,7)

    def test_calibration_reliability_failure(self):
        m=self.manifest(); u=calibrate_manifest(m,{"success":False},alpha=.5)
        self.assertLess(u.reliability,m.reliability)

    def test_calibration_bad_alpha(self):
        with self.assertRaises(ValueError):
            calibrate_manifest(self.manifest(),{},alpha=0)

    def test_semantic_graph_has_all_kinds(self):
        reg=CapabilityRegistry([self.manifest()])
        task=TaskContract("t","p","data.hash.sha256",inputs={"data":"x"})
        d=CapabilityPlanner(reg).plan(task,self.auth(),now_epoch=1000)
        g=build_semantic_graph(task,d)
        self.assertEqual({r["kind"] for r in g["records"]},{"D","I","K","W","P"})
        self.assertEqual(len(g["allowed_route_kinds"]),25)

    def test_run_task_outputs_certificate(self):
        reg=CapabilityRegistry([self.manifest()])
        task=TaskContract("t","p","data.hash.sha256",inputs={"data":"x"})
        with tempfile.TemporaryDirectory() as d:
            cert=run_task(task,reg,self.auth(),d,now_epoch=1000)
            self.assertTrue(cert["ledger_valid"])
            self.assertTrue((Path(d)/"minex_certificate.json").exists())

    def test_run_task_paid_is_dry_run_money(self):
        m=CapabilityManifest("c","c","data.hash.sha256","REMOTE_API","p","n","1",monetary_cost_base=.2,executor="builtin")
        reg=CapabilityRegistry([m]); task=TaskContract("t","p","data.hash.sha256",inputs={"data":"x"})
        with tempfile.TemporaryDirectory() as d:
            cert=run_task(task,reg,self.auth(),d,now_epoch=1000)
            self.assertFalse(cert["settlement"]["real_funds_moved"])

    def test_composite_parallel(self):
        reg=CapabilityRegistry([self.manifest()])
        task=TaskContract("t","p","composite",constraints={"parallel":True},subtasks=[
            {"operation":"data.hash.sha256","purpose":"a","inputs":{"data":"a"}},
            {"operation":"data.hash.sha256","purpose":"b","inputs":{"data":"b"}},
        ])
        with tempfile.TemporaryDirectory() as d:
            cert=run_composite_task(task,reg,self.auth(),d,now_epoch=1000)
            self.assertTrue(cert["parallel"])
            self.assertEqual(cert["subtask_count"],2)

    def test_no_external_authority(self):
        reg=CapabilityRegistry([self.manifest()]); task=TaskContract("t","p","data.hash.sha256",inputs={"data":"x"})
        with tempfile.TemporaryDirectory() as d:
            cert=run_task(task,reg,self.auth(),d,now_epoch=1000)
            self.assertEqual(cert["automatic_external_action_authority"],0)


if __name__ == "__main__":
    unittest.main()

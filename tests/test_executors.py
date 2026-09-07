import unittest

from minex_fabric.executors import ExecutionError, execute_builtin, safe_eval


class ExecutorTests(unittest.TestCase):
    def test_safe_eval(self):
        self.assertEqual(safe_eval("x*2+1", {"x":3}), 7)

    def test_safe_eval_blocks_attribute(self):
        with self.assertRaises(ExecutionError):
            safe_eval("x.__class__", {"x":3})

    def test_safe_eval_blocks_import(self):
        with self.assertRaises((ExecutionError, SyntaxError)):
            safe_eval("__import__('os')", {})

    def test_text_normalize(self):
        r = execute_builtin("text.normalize", {"text":" a   b\n c "})
        self.assertEqual(r["text"], "a b c")

    def test_summary(self):
        r = execute_builtin("text.summarize.extractive", {"text":"Alpha beta. Alpha gamma. Delta.","sentences":1})
        self.assertEqual(r["selected_sentence_count"],1)

    def test_csv_profile(self):
        r = execute_builtin("csv.profile", {"csv_text":"a,b\n1,x\n2,y\n"})
        self.assertEqual(r["rows"],2)
        self.assertEqual(r["column_profiles"]["a"]["type"],"numeric")

    def test_temperature(self):
        r = execute_builtin("unit.convert.temperature", {"value":100,"from":"C","to":"F"})
        self.assertEqual(r["result"],212)

    def test_hash(self):
        r = execute_builtin("data.hash.sha256", {"data":"abc"})
        self.assertEqual(len(r["sha256"]),64)

    def test_json_select(self):
        r = execute_builtin("json.select", {"object":{"a":1,"b":2},"keys":["b"]})
        self.assertEqual(r["object"],{"b":2})

    def test_report_compose(self):
        r = execute_builtin("report.compose.markdown", {"title":"T","sections":[{"heading":"H","body":"B"}]})
        self.assertIn("# T",r["markdown"])
        self.assertEqual(r["section_count"],1)

    def test_unknown_operation(self):
        with self.assertRaises(ExecutionError):
            execute_builtin("unknown", {})


if __name__ == "__main__":
    unittest.main()

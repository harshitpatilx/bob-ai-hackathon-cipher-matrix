import json
import tempfile
import unittest
from pathlib import Path

from cfna.pipeline import build_case, analyze, run_case

DATA = Path(__file__).resolve().parents[1] / "data" / "cases"
CASES = sorted(p.name for p in DATA.iterdir() if p.is_dir()) if DATA.exists() else []


@unittest.skipUnless(CASES, "trial data not generated - run: python -m cfna.datagen")
class TestEndToEnd(unittest.TestCase):
    def test_trial_passes(self) -> None:
        import subprocess
        import sys

        root = Path(__file__).resolve().parents[1]
        proc = subprocess.run(
            [sys.executable, "-m", "cfna", "trial"],
            cwd=root, capture_output=True, text=True, timeout=600,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)
        self.assertIn("OVERALL: 3/3 PASS", proc.stdout)

    def test_run_exports_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_case(DATA / CASES[0], Path(tmp))
            out = Path(result["out_dir"])
            for name in ("report.html", "fir_brief.md", "case_data.json", "network.json"):
                self.assertTrue((out / name).exists(), f"missing {name}")
            data = json.loads((out / "case_data.json").read_text(encoding="utf-8"))
            brief = data["brief"]
            self.assertTrue(brief["patterns"])
            self.assertEqual(brief["patterns"][0]["id"], "SIM_SWAP_OTP")
            html = (out / "report.html").read_text(encoding="utf-8")
            self.assertIn("vis-network", html)
            self.assertIn("FIR", html)

    def test_report_contains_evidence(self) -> None:
        case, _ = build_case(DATA / "jamtara_sim_swap")
        brief, _metrics, evidence = analyze(case)
        self.assertIsNotNone(brief.primary)
        self.assertGreaterEqual(len(evidence["sim_swap_bindings"]), 1)
        self.assertGreater(len(evidence["largest_transfers"]), 0)
        self.assertGreater(len(evidence["victims"]), 0)
        self.assertTrue(brief.assessments)


if __name__ == "__main__":
    unittest.main()

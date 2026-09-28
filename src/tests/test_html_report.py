import re
import shutil
import subprocess
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

from cfna.pipeline import run_case

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "cases"
VOID = {"meta", "link", "br", "hr", "img", "input", "source", "path", "circle", "line", "stop", "col"}


class _Checker(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(f"stray </{tag}>")
        elif self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            while self.stack and self.stack[-1] != tag:
                self.errors.append(f"unclosed <{self.stack.pop()}> before </{tag}>")
            self.stack.pop()
        else:
            self.errors.append(f"unexpected </{tag}>")


def _render(tmp: str, case_name: str) -> str:
    result = run_case(DATA / case_name, Path(tmp))
    return (Path(result["out_dir"]) / "report.html").read_text(encoding="utf-8")


@unittest.skipUnless(DATA.exists(), "trial data not generated - run: python -m cfna.datagen")
class TestTemplateReport(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import tempfile as _tempfile

        cls._tmp = _tempfile.TemporaryDirectory()
        cls.html = _render(cls._tmp.name, "jamtara_sim_swap")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_template_structure(self) -> None:
        self.assertIn('<nav id="navbar">', self.html)
        self.assertIn('class="hero"', self.html)
        self.assertIn('class="stats-grid"', self.html)
        self.assertIn('class="charts-grid"', self.html)
        self.assertIn('class="graph-card"', self.html)
        self.assertIn('class="tree"', self.html)
        self.assertIn('id="evidence"', self.html)
        self.assertIn('id="fir"', self.html)
        self.assertIn("TemplateMo", self.html)
        self.assertEqual(self.html.count("<section"), 7)

    def test_template_css_inlined(self) -> None:
        css = self.html.split("<style>", 1)[1].split("</style>", 1)[0]
        self.assertGreater(len(css), 15000)
        self.assertIn("#0a0e27", css)
        self.assertIn("TemplateMo 602 Graph Page", css)
        self.assertEqual(css.count("{"), css.count("}"))

    def test_tag_balance(self) -> None:
        parser = _Checker()
        parser.feed(self.html)
        problems = list(parser.errors) + [f"unclosed <{t}>" for t in parser.stack]
        self.assertEqual(problems, [])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_inline_js_syntax(self) -> None:
        scripts = re.findall(r"<script>(.*?)</script>", self.html, re.S)
        self.assertEqual(len(scripts), 1)
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
            fh.write(scripts[0])
            tmp = fh.name
        try:
            proc = subprocess.run(["node", "--check", tmp], capture_output=True, text=True, timeout=60)
            self.assertEqual(proc.returncode, 0, proc.stderr)
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_case_data_still_exported(self) -> None:
        import json

        out = Path(self._tmp.name) / "jamtara_sim_swap"
        for name in ("report.html", "fir_brief.md", "case_data.json", "network.json"):
            self.assertTrue((out / name).exists(), name)
        data = json.loads((out / "case_data.json").read_text(encoding="utf-8"))
        self.assertEqual(data["brief"]["patterns"][0]["id"], "SIM_SWAP_OTP")


if __name__ == "__main__":
    unittest.main()

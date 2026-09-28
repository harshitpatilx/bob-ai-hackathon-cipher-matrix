"""Tests for the browser input form (`python -m cfna serve`).

The server is a plain stdlib ThreadingHTTPServer, so these tests start it on an ephemeral
port in-process and drive it with http.client - no browser, no network, no external calls.
"""
from __future__ import annotations

import http.client
import json
import re
import shutil
import subprocess
import tempfile
import threading
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode

from cfna.config import INPUT_UI_PORT, INPUT_UI_URL
from cfna.serve import App, create_server, render_input_page

ROOT = Path(__file__).resolve().parents[1]
VOID = {"meta", "link", "br", "hr", "img", "input", "source", "path", "circle", "line",
        "stop", "col", "svg", "text"}


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


def _balance(html: str) -> list[str]:
    parser = _Checker()
    parser.feed(html)
    return list(parser.errors) + [f"unclosed <{t}>" for t in parser.stack]


NOTES = (
    "KEY FINDING: the victim SIM was reissued after a spoofed KYC update and the ported SIM "
    "was used to read OTPs, after which UPI debits were executed from account 5001000123456 "
    "to mule account 5001000987654 and then withdrawn immediately.\n\n"
    "Kingpin Anup Saha controls the cashout account 5001000000001. Recruiter Suraj Ekka "
    "sourced the rented bank accounts. Victim Ramesh Kumar (9431100001) complained of a loss "
    "of Rs.64,000 on 06/03/2024 after the caller warned that the account blocked."
)

TABLE = (
    "timestamp,txn_id,from_account,to_account,amount_inr,channel,remarks\n"
    "2024-03-06T10:05:00,T1001,5001000123456,5001000987654,64000,UPI,fraud debit\n"
    "2024-03-06T10:20:00,T1002,5001000987654,5001000000001,60000,UPI,cashout\n"
)


class ServeTestCase(unittest.TestCase):
    """Shared live server: one ephemeral port, one temp destination tree."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        base = Path(cls._tmp.name)
        cls.dest = base / "cases"
        cls.out = base / "output"
        cls.server = create_server("127.0.0.1", 0, cls.dest, cls.out)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)
        cls._tmp.cleanup()

    # ------------------------------------------------------------- http helpers
    @classmethod
    def _request(cls, method: str, path: str, body: bytes | None = None,
                 headers: dict[str, str] | None = None):
        conn = http.client.HTTPConnection("127.0.0.1", cls.port, timeout=60)
        try:
            conn.request(method, path, body=body, headers=headers or {})
            response = conn.getresponse()
            payload = response.read()
            return response.status, dict(response.getheaders()), payload
        finally:
            conn.close()

    @classmethod
    def get(cls, path: str):
        return cls._request("GET", path)

    @classmethod
    def post_form(cls, path: str, fields: dict[str, str]):
        body = urlencode(fields).encode("utf-8")
        return cls._request("POST", path, body, {
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": str(len(body)),
        })

    @staticmethod
    def text(payload: bytes) -> str:
        return payload.decode("utf-8", errors="replace")


class TestInputPage(ServeTestCase):
    def test_root_serves_the_form(self) -> None:
        status, headers, payload = self.get("/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", headers.get("Content-Type", ""))
        page = self.text(payload)
        self.assertIn('<form class="contact-form" method="post" action="/analyze"', page)
        self.assertIn('name="notes"', page)
        self.assertIn('name="table"', page)
        self.assertIn('id="reports"', page)
        self.assertIn('href="/static/graph-page.css"', page)
        self.assertIn('href="/static/cfna.css"', page)

    def test_every_metadata_field_is_present(self) -> None:
        from cfna.intake import META_FIELDS

        page = self.text(self.get("/")[2])
        for key, _label in META_FIELDS:
            if key == "notes":
                continue
            self.assertIn(f'name="{key}"', page)

    def test_form_is_balanced_html(self) -> None:
        page = self.text(self.get("/")[2])
        self.assertEqual(_balance(page), [])

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_inline_js_syntax(self) -> None:
        scripts = re.findall(r"<script>(.*?)</script>", self.text(self.get("/")[2]), re.S)
        self.assertGreaterEqual(len(scripts), 1)
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
            for script in scripts:
                fh.write(script)
                fh.write("\n")
            tmp = fh.name
        try:
            proc = subprocess.run(["node", "--check", tmp], capture_output=True, text=True, timeout=60)
            self.assertEqual(proc.returncode, 0, proc.stderr)
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_error_message_is_escaped_and_form_keeps_values(self) -> None:
        page = render_input_page(
            App(Path("data/web_cases"), Path("output")),
            error='<script>alert("x")</script>',
            values={"title": "A & B"},
        )
        self.assertNotIn('<script>alert("x")</script>', page)
        self.assertIn("&lt;script&gt;", page)
        self.assertIn('value="A &amp; B"', page)
        self.assertEqual(_balance(page), [])

    def test_reports_section_starts_empty(self) -> None:
        page = self.text(self.get("/")[2])
        self.assertIn("No reports yet", page)


class TestStaticAndMeta(ServeTestCase):
    def test_stylesheets_are_served(self) -> None:
        for name, needle in (("graph-page.css", "#0a0e27"), ("cfna.css", ".chip")):
            status, headers, payload = self.get(f"/static/{name}")
            self.assertEqual(status, 200, name)
            self.assertIn("text/css", headers.get("Content-Type", ""), name)
            self.assertIn(needle, self.text(payload))

    def test_unknown_asset_404(self) -> None:
        self.assertEqual(self.get("/static/../serve.py")[0], 404)
        self.assertEqual(self.get("/static/nope.css")[0], 404)

    def test_health_probe(self) -> None:
        status, _, payload = self.get("/health")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(payload), {"ok": True, "backend": "local", "coins": 0})

    def test_unknown_route_404(self) -> None:
        self.assertEqual(self.get("/nope")[0], 404)
        self.assertEqual(self.get("/report/")[0], 404)


class TestAnalyzeFlow(ServeTestCase):
    case_id = "web_form_case"

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.status, cls.headers, cls.payload = cls.post_form("/analyze", {
            "title": "Web form SIM swap case",
            "case_id": cls.case_id,
            "police_station": "Cyber Crime Police Station",
            "district": "Kolkata",
            "state": "West Bengal",
            "notes": NOTES,
            "table": TABLE,
        })

    def test_redirects_to_the_report(self) -> None:
        self.assertEqual(self.status, 303, self.text(self.payload))
        self.assertEqual(
            self.headers.get("Location"),
            f"/report/{self.case_id}/report.html",
        )

    def test_case_folder_written_under_dest(self) -> None:
        case_dir = self.dest / self.case_id
        self.assertTrue((case_dir / "case.json").is_file())
        meta = json.loads((case_dir / "case.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["title"], "Web form SIM swap case")
        self.assertEqual(meta["case_id"], self.case_id)
        files = sorted(p.name for p in case_dir.iterdir() if p.is_file())
        self.assertTrue(any(name.endswith(".txt") for name in files), files)
        self.assertTrue(any(name.endswith(".csv") for name in files), files)

    def test_report_generated_and_served(self) -> None:
        location = self.headers["Location"]
        status, headers, payload = self.get(location)
        self.assertEqual(status, 200)
        self.assertIn("text/html", headers.get("Content-Type", ""))
        page = self.text(payload)
        self.assertIn("Web form SIM swap case", page)
        self.assertIn("TemplateMo", page)
        self.assertEqual(_balance(page), [])
        self.assertTrue((self.out / self.case_id / "report.html").is_file())
        self.assertTrue((self.out / self.case_id / "fir_brief.md").is_file())

    def test_fir_brief_downloadable(self) -> None:
        status, _, payload = self.get(f"/report/{self.case_id}/fir_brief.md")
        self.assertEqual(status, 200)
        self.assertIn("FIR", self.text(payload))

    def test_case_appears_in_api_listing(self) -> None:
        status, _, payload = self.get("/api/cases")
        self.assertEqual(status, 200)
        self.assertIn(self.case_id, json.loads(payload)["cases"])

    def test_case_link_shown_on_the_form(self) -> None:
        page = self.text(self.get("/")[2])
        self.assertIn(f'/report/{self.case_id}/report.html', page)


class TestAnalyzeValidation(ServeTestCase):
    def test_empty_submission_is_rejected(self) -> None:
        status, _, payload = self.post_form("/analyze", {"title": "Empty case"})
        self.assertEqual(status, 400)
        page = self.text(payload)
        self.assertIn("Nothing to analyze", page)
        self.assertIn('value="Empty case"', page)

    def test_json_table_is_kept_as_json(self) -> None:
        case_id = "web_json_case"
        records = json.dumps([
            {"timestamp": "2024-03-06T10:05:00", "from_account": "5001000123456",
             "to_account": "5001000987654", "amount_inr": 64000},
        ])
        status, headers, _ = self.post_form("/analyze", {
            "title": "JSON export case",
            "case_id": case_id,
            "notes": NOTES,
            "table": records,
        })
        self.assertEqual(status, 303, headers)
        case_dir = self.dest / case_id
        payload_files = [p for p in case_dir.glob("*.json") if p.name != "case.json"]
        self.assertEqual(len(payload_files), 1, sorted(p.name for p in case_dir.iterdir()))
        self.assertIn("web_records", payload_files[0].name)
        records_back = json.loads(payload_files[0].read_text(encoding="utf-8"))
        self.assertEqual(records_back[0]["amount_inr"], 64000)

    def test_bundled_trial_cases_are_protected(self) -> None:
        trial = self.dest / "jamtara_sim_swap"
        trial.mkdir(parents=True, exist_ok=True)
        (trial / "truth.json").write_text("{}", encoding="utf-8")
        try:
            status, _, payload = self.post_form("/analyze", {
                "title": "Should not run",
                "case_id": "jamtara_sim_swap",
                "notes": NOTES,
            })
            self.assertEqual(status, 400)
            self.assertIn("bundled trial", self.text(payload))
        finally:
            shutil.rmtree(trial, ignore_errors=True)

    def test_resubmitting_same_id_replaces_the_case(self) -> None:
        case_id = "web_resubmit"
        first = self.post_form("/analyze", {"title": "First", "case_id": case_id, "notes": NOTES})
        self.assertEqual(first[0], 303, first[0])
        stray = self.dest / case_id / "stale_notes.txt"
        stray.write_text("stale", encoding="utf-8")
        second = self.post_form("/analyze", {"title": "Second", "case_id": case_id, "notes": NOTES})
        self.assertEqual(second[0], 303, second[0])
        self.assertFalse(stray.exists())
        meta = json.loads((self.dest / case_id / "case.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["title"], "Second")


class TestReportSafety(ServeTestCase):
    def test_missing_report_404(self) -> None:
        self.assertEqual(self.get("/report/does_not_exist/report.html")[0], 404)

    def test_path_traversal_is_blocked(self) -> None:
        for path in (
            "/report/../cli.py",
            "/report/x/../../serve.py",
            "/report/%2e%2e%2f%2e%2e%2fcli.py",
        ):
            self.assertEqual(self.get(path)[0], 404, path)

    def test_post_to_unknown_endpoint_404(self) -> None:
        self.assertEqual(self.post_form("/nope", {"a": "b"})[0], 404)


class TestReportLinksBackToInput(unittest.TestCase):
    """The generated report must keep pointing at the input form (and stay 7 sections)."""

    @classmethod
    def setUpClass(cls) -> None:
        data = ROOT / "data" / "cases"
        if not data.exists():
            raise unittest.SkipTest("trial data not generated - run: python -m cfna.datagen")
        cls._tmp = tempfile.TemporaryDirectory()
        from cfna.pipeline import run_case

        result = run_case(data / "jamtara_sim_swap", Path(cls._tmp.name))
        cls.html = (Path(result["out_dir"]) / "report.html").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        if hasattr(cls, "_tmp"):
            cls._tmp.cleanup()

    def test_nav_links_to_the_input_form(self) -> None:
        self.assertIn(f'<a href="{INPUT_UI_URL}" target="_blank" rel="noopener">New case</a>',
                      self.html)

    def test_nav_anchor_matches_configured_port(self) -> None:
        self.assertTrue(INPUT_UI_URL.startswith("http://127.0.0.1:"))
        self.assertTrue(INPUT_UI_URL.endswith(f":{INPUT_UI_PORT}/"))
        self.assertIn(INPUT_UI_URL, self.html)


class TestBareCommand(unittest.TestCase):
    """`python -m cfna` with no arguments must be the friendliest entry point: the form."""

    @staticmethod
    def _main(argv: list[str]) -> int:
        import contextlib
        import io

        from cfna.cli import main

        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            return main(argv)

    def test_no_arguments_starts_the_form(self) -> None:
        from unittest import mock

        with mock.patch("cfna.serve.serve", return_value=0) as serve:
            self.assertEqual(self._main([]), 0)
        kwargs = serve.call_args.kwargs
        self.assertEqual(kwargs["host"], "127.0.0.1")
        self.assertEqual(kwargs["port"], INPUT_UI_PORT)
        self.assertTrue(kwargs["open_browser"])

    def test_serve_flags_are_forwarded(self) -> None:
        from unittest import mock

        with mock.patch("cfna.serve.serve", return_value=0) as serve:
            self.assertEqual(self._main(["serve", "--port", "9001", "--no-browser"]), 0)
        self.assertEqual(serve.call_args.kwargs["port"], 9001)
        self.assertFalse(serve.call_args.kwargs["open_browser"])

    def test_unknown_command_still_fails(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            self._main(["bogus"])
        self.assertEqual(ctx.exception.code, 2)

    def test_help_still_works(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            self._main(["--help"])
        self.assertEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()

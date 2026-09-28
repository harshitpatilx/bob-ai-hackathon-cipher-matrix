"""Local browser input form for CFNA.

`python -m cfna serve` starts a localhost-only HTTP server (stdlib, no dependencies, no
framework) that offers a form for pasting your own case material and runs the exact same
pipeline the CLI uses:

    GET  /                     the input form (TemplateMo "Graph Page" styling)
    POST /analyze              form -> cfna.intake -> pipeline -> report
    GET  /report/<id>/<file>   read-only view of a generated report
    GET  /static/<css>         the two shipped stylesheets
    GET  /api/cases            JSON list of generated reports
    GET  /health               liveness probe

Nothing outside this module and one CLI registration changes: `run`, `new`, `batch`, `trial`
and the generated `report.html` all behave exactly as before. The server binds to 127.0.0.1
by default and never makes an outbound request.
"""
from __future__ import annotations

import json
import re
import shutil
import threading
import webbrowser
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from cfna import config as cfg
from cfna.intake import META_FIELDS, slugify, write_case
from cfna.pipeline import run_case

ASSETS = Path(__file__).resolve().parent / "report" / "assets"
DEFAULT_HOST = cfg.INPUT_UI_HOST
DEFAULT_PORT = cfg.INPUT_UI_PORT
MAX_BODY = 4 * 1024 * 1024
SERVED_CSS = ("graph-page.css", "cfna.css")
REPORT_FILES = {"report.html", "fir_brief.md", "case_data.json", "network.json"}
CASE_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")

# intake.META_FIELDS minus the free-text "notes" field, which gets its own textarea.
META_INPUTS: list[tuple[str, str]] = [pair for pair in META_FIELDS if pair[0] != "notes"]

INPUT_CSS = """
.form-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 18px; }
.form-grid { display: grid; gap: 0; }
.form-grid .form-group { margin-bottom: 18px; }
.form-note { font-size: 13px; color: #8b93b5; margin-top: 8px; line-height: 1.6; }
.file-row { display: flex; align-items: center; gap: 12px; margin-top: 10px; flex-wrap: wrap; }
.file-btn { display: inline-block; padding: 8px 16px; font-size: 13px; cursor: pointer;
  border: 1px dashed rgba(0, 255, 204, 0.5); border-radius: 8px; color: #00ffcc; }
.file-btn:hover { background: rgba(0, 255, 204, 0.08); }
.file-row input[type=file] { display: none; }
.file-name { font-size: 12px; color: #8b93b5; }
.alert { padding: 14px 18px; border-radius: 10px; font-size: 14px; margin-bottom: 22px; line-height: 1.5; }
.alert-error { background: rgba(255, 107, 107, 0.12); border: 1px solid rgba(255, 107, 107, 0.5); color: #ffb3b3; }
.alert-ok { background: rgba(0, 255, 204, 0.1); border: 1px solid rgba(0, 255, 204, 0.4); color: #9dffe9; }
.submit-row { margin-top: 26px; display: flex; gap: 16px; align-items: center; flex-wrap: wrap; }
.submit-row button { border: 0; cursor: pointer; font-family: inherit; }
.ghost-link { color: #00ffcc; font-size: 14px; text-decoration: none; border-bottom: 1px dashed rgba(0,255,204,.5); }
.info-list { list-style: none; padding: 0; margin: 18px 0 0; }
.info-list li { position: relative; padding-left: 22px; margin-bottom: 12px; font-size: 14px; color: #c3c9e6; line-height: 1.6; }
.info-list li::before { content: '>'; position: absolute; left: 0; color: #00ffcc; font-weight: 700; }
pre.snippet { background: rgba(0, 0, 0, 0.35); border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px; padding: 14px 16px; overflow-x: auto; font-size: 12.5px; line-height: 1.6;
  color: #9dffe9; margin: 16px 0 0; }
.reports-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }
.report-link { display: block; padding: 16px 18px; border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px; background: rgba(255, 255, 255, 0.03); color: #ffffff; text-decoration: none; }
.report-link:hover { border-color: rgba(0, 255, 204, 0.5); }
.report-link .rl-title { display: block; font-weight: 600; margin-bottom: 6px; }
.report-link .rl-sub { font-size: 12px; color: #8b93b5; }
.empty { color: #8b93b5; font-size: 14px; padding: 18px; border: 1px dashed rgba(255,255,255,.14);
  border-radius: 12px; }
"""

PAGE_SCRIPT = """
document.querySelectorAll('input[type=file][data-target]').forEach(function (inp) {
  inp.addEventListener('change', function () {
    var file = inp.files && inp.files[0];
    if (!file) return;
    var reader = new FileReader();
    reader.onload = function () {
      var box = document.getElementById(inp.getAttribute('data-target'));
      if (box) box.value = String(reader.result || '');
    };
    reader.readAsText(file);
    var label = inp.parentElement.querySelector('.file-name');
    if (label) label.textContent = file.name;
  });
});
"""


class App:
    """Owns the input -> case -> report flow for the web form."""

    def __init__(self, dest: Path, out: Path) -> None:
        self.dest = dest
        self.out = out

    def cases(self) -> list[str]:
        if not self.out.is_dir():
            return []
        return sorted(
            p.parent.name for p in self.out.glob("*/report.html")
        )

    def analyze(self, fields: dict[str, str]) -> str:
        meta = {key: (fields.get(key) or "").strip() for key, _ in META_INPUTS}
        notes = (fields.get("notes") or "").strip()
        table = (fields.get("table") or "").strip()
        if not notes and not table:
            raise ValueError(
                "Nothing to analyze - paste the narrative notes and/or a CSV table first."
            )
        if not meta.get("title"):
            meta["title"] = "Untitled Cyber Fraud Case"
        case_id = slugify(meta.get("case_id") or meta["title"])
        meta["case_id"] = case_id

        case_dir = self.dest / case_id
        if (case_dir / "truth.json").exists():
            raise ValueError(
                f"'{case_id}' is a bundled trial case - pick a different case id."
            )
        if case_dir.exists():
            shutil.rmtree(case_dir)
        texts = [("web_notes", notes)] if notes else []
        tables = [("web_records", table)] if table else []
        write_case(case_dir, meta, texts, tables, [])
        run_case(case_dir, self.out)
        return case_id


def _field_html(name: str, label: str, value: str) -> str:
    return (
        f'<div class="form-group">'
        f'<label for="f_{name}">{escape(label)}</label>'
        f'<input type="text" id="f_{name}" name="{name}" value="{escape(value, quote=True)}" autocomplete="off">'
        f"</div>"
    )


def render_input_page(
    app: App,
    error: str = "",
    values: dict[str, str] | None = None,
    status: str = "",
) -> str:
    values = values or {}
    fields = "".join(_field_html(name, label, values.get(name, "")) for name, label in META_INPUTS)
    cases = app.cases()
    if cases:
        links = "".join(
            f'<a class="report-link" href="/report/{escape(case_id, quote=True)}/report.html">'
            f'<span class="rl-title">{escape(case_id.replace("_", " ").title())}</span>'
            f'<span class="rl-sub">open report &rarr;</span></a>'
            for case_id in cases
        )
        reports = f'<div class="reports-list">{links}</div>'
    else:
        reports = '<div class="empty">No reports yet - submit the form above and yours appears here.</div>'

    alert = ""
    if error:
        alert = f'<div class="alert alert-error">{escape(error)}</div>'
    elif status:
        alert = f'<div class="alert alert-ok">{escape(status)}</div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CFNA &mdash; New case input</title>
<link rel="stylesheet" href="/static/graph-page.css">
<link rel="stylesheet" href="/static/cfna.css">
<style>
{INPUT_CSS}
</style>
</head>
<body>
<nav id="navbar">
  <div class="nav-container">
    <a href="/" class="logo">
      <div class="logo-icon">
        <svg viewBox="0 0 24 24"><path d="M3 13h2v8H3zm4-8h2v13H7zm4-2h2v15h-2zm4 4h2v11h-2zm4-2h2v13h-2z"/></svg>
      </div>
      <span class="logo-text">CFNA</span>
    </a>
    <ul class="nav-links">
      <li><a href="#input" class="active">New case</a></li>
      <li><a href="#reports">Reports</a></li>
      <li><a href="#how">How it works</a></li>
    </ul>
    <div class="hamburger" id="hamburger"><span></span><span></span><span></span></div>
  </div>
  <ul class="nav-links-mobile" id="navLinksMobile">
    <li><a href="#input">New case</a></li>
    <li><a href="#reports">Reports</a></li>
    <li><a href="#how">How it works</a></li>
  </ul>
</nav>

<header class="hero">
  <div class="hero-bg"></div>
  <div class="hero-content">
    <div class="hero-text">
      <p class="kicker">Bob-powered cyber fraud network analyzer</p>
      <h1>Paste your own case<br>and get an FIR-ready brief</h1>
      <p class="hero-sub">Everything runs locally in this process: deterministic extraction,
        pattern classification, hierarchy mapping and the report. No upload, no external calls,
        0 coins consumed.</p>
      <div class="chips">
        <span class="chip">localhost only</span>
        <span class="chip">stdlib python</span>
        <span class="chip">same pipeline as the CLI</span>
      </div>
    </div>
  </div>
</header>

<section id="input" class="contact-section">
  <div class="contact-grid">
    <form class="contact-form" method="post" action="/analyze">
      {alert}
      <div class="form-row">
        {fields}
      </div>

      <div class="form-group">
        <label for="notes">Narrative notes *</label>
        <textarea id="notes" name="notes" rows="8"
          placeholder="Paste incident notes, victim complaints or accused statements. Identifiers (accounts, UPI, phone, IMEI, ICCID) and roles (kingpin, recruiter, mule, victim) are picked up automatically.">{escape(values.get("notes", ""))}</textarea>
        <div class="file-row">
          <label class="file-btn">Load a text file
            <input type="file" accept=".txt,.md,.log,.statement,.json,.csv" data-target="notes">
          </label>
          <span class="file-name">no file selected</span>
        </div>
        <p class="form-note">One paragraph is enough. Include amounts as Rs.64000 and dates as 06/03/2024.</p>
      </div>

      <div class="form-group">
        <label for="table">Transaction / CDR / SIM table (optional)</label>
        <textarea id="table" name="table" rows="6"
          placeholder="Header row first, comma or tab separated - e.g. timestamp,txn_id,from_account,to_account,amount_inr,channel">{escape(values.get("table", ""))}</textarea>
        <div class="file-row">
          <label class="file-btn">Load a CSV / JSON file
            <input type="file" accept=".csv,.tsv,.txt,.json,.jsonl" data-target="table">
          </label>
          <span class="file-name">no file selected</span>
        </div>
        <p class="form-note">Column kind is sniffed from the header, so bank and wallet exports drop in as-is.</p>
      </div>

      <div class="submit-row">
        <button type="submit" class="cta-button">Analyze &amp; build report</button>
        <a class="ghost-link" href="/">clear form</a>
      </div>
    </form>

    <div id="how" class="contact-info">
      <h3 class="info-title">How this works</h3>
      <ul class="info-list">
        <li>Submit the form &rarr; a case folder is written under <code>{cfg.DEFAULT_WEB_CASES_SUBDIR}/</code>.</li>
        <li>The same pipeline runs: extract &rarr; metrics &rarr; pattern &rarr; hierarchy &rarr; risk &rarr; evidence.</li>
        <li>The generated <code>report.html</code> opens right here, with the FIR brief beside it.</li>
        <li>Re-submitting the same case id replaces it; bundled trial cases are protected.</li>
      </ul>
      <p class="form-note">Prefer the terminal? The same input is one command:</p>
      <pre class="snippet">python -m cfna new --title "My case" --text-file notes.txt --file txns.csv
python -m cfna new            # interactive wizard
python -m cfna template .     # example input files</pre>
      <p class="form-note">Server: <code>{escape(DEFAULT_HOST)}:{DEFAULT_PORT}</code> &middot;
        stop it with <code>Ctrl+C</code> in the terminal that started it.</p>
    </div>
  </div>
</section>

<section id="reports" class="reports-section">
  <h2 class="section-title">Generated reports</h2>
  {reports}
</section>

<footer class="contact-section" style="padding-top:0">
  <div class="copyright">
    <p>CFNA &mdash; Bob-powered Cyber Fraud Network Analyzer. Layout based on
      <a href="https://templatemo.com/tm-602-graph-page" target="_blank" rel="noopener">TemplateMo 602 Graph Page</a>.</p>
  </div>
</footer>

<script>
{PAGE_SCRIPT}
</script>
<script>
(function () {{
  var h = document.getElementById('hamburger'), m = document.getElementById('navLinksMobile');
  if (h && m) h.addEventListener('click', function () {{ m.classList.toggle('open'); }});
}})();
</script>
</body>
</html>"""


def _error_page(message: str, code: int) -> str:
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>CFNA error {code}</title>
<style>body{{background:#0a0e27;color:#fff;font-family:Segoe UI,Arial,sans-serif;padding:60px}}
a{{color:#00ffcc}}</style></head><body>
<h1>Error {code}</h1><p>{escape(message)}</p><p><a href="/">&larr; back to the input form</a></p>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    server_version = "cfna-serve/1.0"

    @property
    def app(self) -> App:
        return self.server.app  # type: ignore[attr-defined]

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: D102
        pass  # keep the console clean; the CLI prints its own banner

    # ---------------------------------------------------------------- responses
    def _send(self, code: int, body: bytes, content_type: str, extra: list[tuple[str, str]] | None = None) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        for key, value in extra or []:
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _html(self, code: int, page: str) -> None:
        self._send(code, page.encode("utf-8"), "text/html; charset=utf-8")

    def _json(self, code: int, payload: Any) -> None:
        self._send(code, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _redirect(self, location: str) -> None:
        self._send(303, b"", "text/plain; charset=utf-8", [("Location", location)])

    # ---------------------------------------------------------------------- GET
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        try:
            if path in ("/", ""):
                self._html(200, render_input_page(self.app))
            elif path.startswith("/static/"):
                self._serve_static(path.split("/static/", 1)[1])
            elif path.startswith("/report/"):
                self._serve_report(path[len("/report/"):])
            elif path == "/api/cases":
                self._json(200, {"cases": self.app.cases()})
            elif path == "/health":
                self._json(200, {"ok": True, "backend": "local", "coins": 0})
            else:
                self._html(404, _error_page("No such page.", 404))
        except BrokenPipeError:
            pass
        except Exception as exc:  # noqa: BLE001 - never kill the server on a bad request
            self.log_error("%s", exc)
            self._html(500, _error_page(f"Server error: {exc}", 500))

    def _serve_static(self, name: str) -> None:
        if name not in SERVED_CSS:
            self._html(404, _error_page("Unknown asset.", 404))
            return
        path = ASSETS / name
        if not path.is_file():
            self._html(404, _error_page("Asset not shipped with this build.", 404))
            return
        self._send(200, path.read_bytes(), "text/css; charset=utf-8",
                   [("Cache-Control", "public, max-age=300")])

    def _serve_report(self, rest: str) -> None:
        case_id, _, filename = rest.partition("/")
        case_id = case_id.strip("/")
        filename = filename or "report.html"
        # strict name validation first: case ids are slugs, and only generated outputs are
        # ever handed out - "..", separators or absolute paths can never reach the filesystem.
        if not CASE_ID_RE.fullmatch(case_id) or filename not in REPORT_FILES:
            self._html(404, _error_page("Report not found - analyze a case first.", 404))
            return
        base = (self.app.out / case_id).resolve()
        target = (base / filename).resolve()
        if target.parent != base or not target.is_file():
            self._html(404, _error_page("Report not found - analyze a case first.", 404))
            return
        ctype = {
            ".html": "text/html; charset=utf-8",
            ".md": "text/markdown; charset=utf-8",
            ".json": "application/json; charset=utf-8",
        }.get(target.suffix.lower(), "application/octet-stream")
        self._send(200, target.read_bytes(), ctype)

    # --------------------------------------------------------------------- POST
    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path != "/analyze":
            self._html(404, _error_page("Unknown endpoint.", 404))
            return
        try:
            fields = self._read_form()
        except ValueError as exc:
            self._html(413, _error_page(str(exc), 413))
            return
        try:
            case_id = self.app.analyze(fields)
        except ValueError as exc:
            self._html(400, render_input_page(self.app, error=str(exc), values=fields))
        except Exception as exc:  # noqa: BLE001 - surface it in the form, keep serving
            self.log_error("analyze failed: %s", exc)
            self._html(500, render_input_page(
                self.app,
                error=f"Analysis failed: {exc}",
                values=fields,
            ))
        else:
            self._redirect(f"/report/{case_id}/report.html")

    def _read_form(self) -> dict[str, str]:
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            raise ValueError(f"Form too large (limit {MAX_BODY // (1024 * 1024)} MB).")
        raw = self.rfile.read(length) if length else b""
        parsed = parse_qs(raw.decode("utf-8", errors="replace"), keep_blank_values=True)
        return {key: values[0] for key, values in parsed.items() if values}


def create_server(host: str, port: int, dest: Path, out: Path) -> ThreadingHTTPServer:
    dest.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    app = App(dest=dest, out=out)
    server = ThreadingHTTPServer((host, port), Handler)
    server.app = app  # type: ignore[attr-defined]
    server.daemon_threads = True
    return server


def serve(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    dest: Path | None = None,
    out: Path | None = None,
    open_browser: bool = True,
) -> int:
    from cfna.cli import DEFAULT_OUT  # imported late: cli imports this module lazily too

    dest = dest or Path.cwd() / cfg.DEFAULT_WEB_CASES_SUBDIR
    out = out or DEFAULT_OUT
    try:
        server = create_server(host, port, dest, out)
    except OSError as exc:
        print(f"error: cannot listen on {host}:{port} ({exc}) - try --port 8766")
        return 2

    bound_host, bound_port = server.server_address[0], server.server_address[1]
    url = f"http://{host}:{bound_port}/"
    print(f"CFNA input form : {url}")
    print(f"  cases -> {dest}")
    print(f"  reports -> {out}")
    print("  stop with Ctrl+C")
    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")
    finally:
        server.server_close()
    return 0

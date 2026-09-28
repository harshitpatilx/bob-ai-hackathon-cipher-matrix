# PLAN — Cyber Fraud Network Analyzer (Bob)

Goal: deterministic, offline analysis of cyber-fraud material into an FIR-ready case brief +
interactive network report, with a seeded mock/trial suite scoring pattern accuracy and role F1.

## Status: complete

| # | Stage | Status |
| --- | --- | --- |
| 1 | Package scaffold (`pyproject.toml`, `cfna/__main__`, CLI) | done |
| 2 | Config: regexes, PSPs, role markers, legal sections, per-pattern actions | done |
| 3 | Models + manual graph algorithms (PageRank, Brandes, communities, hops) | done |
| 4 | Ingest: CSV/text/case.json loading with header-based kind detection | done |
| 5 | Entity extraction: priority span arbitration, person names, labels | done |
| 6 | Relations: structured edges, explicit text links, transfer sentences, co-occurrence | done |
| 7 | Metrics: in/out amounts, pass-through, flow vs call degrees, communities | done |
| 8 | Patterns: 9 detectors (keyword + structural) with per-pattern weights | done |
| 9 | Hierarchy: victims → recruiters → mules → operators → kingpins, mule tiers | done |
| 10 | Risk, timeline, evidence pack (freeze list, SIM-swap table, annexures) | done |
| 11 | Bob layer: local heuristics + `IBM_BOB_ENDPOINT` hook (0 coins consumed) | done |
| 12 | Reports: `fir_brief.md` (12 sections), `report.html` (vis-network) | done |
| 13 | CLI: `run` / `batch` / `trial` / `list` / `patterns` | done |
| 14 | Mock data: 3 seeded cases + `truth.json` ground truth | done |
| 15 | Trial scoring: pattern accuracy + role F1, CI-friendly exit code | done — 3/3 PASS |
| 16 | Tests: 76 unittest cases incl. end-to-end + report validation + intake + web input form | done |
| 17 | README | done |
| 18 | Report redesign on TemplateMo 602 "Graph Page" (assets + renderer) | done |
| 19 | User input: `cfna new` (flags / pipe / interactive wizard), `cfna template`, `run <file>` | done |
| 20 | Narrative-quality fixes: sentence-scoped role labels, owner label propagation, possession + loss links | done |
| 21 | Browser input form: `cfna serve` (localhost page -> intake -> report), nav link from every report | done |
| 22 | Simpler entry point: bare `python -m cfna` = `serve`, plus double-click `start_cfna.bat` | done |

## Verification

```powershell
python -m cfna.datagen          # regenerates data/cases (seeded)
python -m cfna trial -v         # 3/3 PASS, F1 all 1.00, exit 0
python -m unittest discover -s tests -v   # 76 tests OK
python -m cfna run data/cases/jamtara_sim_swap -o output
start output\jamtara_sim_swap\report.html

# simplest: open the tool
start_cfna.bat      (or just: python -m cfna)

# own input, four ways
python -m cfna serve                                          # browser form at http://127.0.0.1:8765/
python -m cfna template .
python -m cfna new --title "My case" --file cfna_input_template\incident_notes.txt --file cfna_input_template\transactions.csv -o output
Get-Content complaint.txt | python -m cfna new --title "Complaint" -o output   # or just: python -m cfna new
```

## User input (`cfna/intake.py`)

`new` materialises whatever you supply into a normal case directory, then runs the same pipeline:

| Source | How |
| --- | --- |
| flags | `--text`, `--text-file`, `--file`, `--table` (all repeatable) + case metadata flags |
| pipe | `Get-Content x.txt \| cfna new ...` (or `--stdin`, `--stdin-format csv` for a table) |
| wizard | `cfna new` in a terminal with no payload flags: metadata → file paths → pasted note (`.`) → pasted table (`END`) |
| example files | `cfna template <dir>` writes `case.json`, `incident_notes.txt`, `transactions.csv`, `call_logs.csv`, `sim_device_registry.csv`, `README.txt` |
| single file | `cfna run some_note.txt` wraps the file into a case first |

`--dest` chooses where the case is created (default `data/cases`), `--no-run` stops after writing,
`--force` adds to an existing case, and a colliding `--id` is refused rather than silently merged.
Stdin is only read when it is the intended source (`--stdin`, or no payload flags), so piping a
file in never blocks on an unused pipe.

## Browser input form (`cfna/serve.py`)

`cfna serve` starts a **localhost-only** `ThreadingHTTPServer` (stdlib, no framework, no outbound
calls) that renders the TemplateMo-styled input page and feeds it straight into the same
`intake -> pipeline -> report` path the CLI uses.

| Route | Behaviour |
| --- | --- |
| `GET /` | form: case metadata fields (from `intake.META_FIELDS`), a notes textarea, a CSV/JSON table textarea, "load file" buttons (FileReader -> textarea, so no multipart handling), plus the list of generated reports |
| `POST /analyze` | urlencoded body -> `write_case` -> `run_case` -> `303 /report/<case_id>/report.html` |
| `GET /report/<id>/<file>` | read-only serving of the four generated outputs (slug-checked names, `..` blocked) |
| `GET /static/<css>` | the two shipped stylesheets; `GET /health`, `GET /api/cases` for probes |

Cases land in `data/web_cases/` (`--dest`) so `batch`/`trial` over `data/cases` are untouched;
re-submitting a case id replaces it (a `truth.json` there is refused). Errors are rendered back
into the form with the values preserved and HTML-escaped. Every generated report's nav carries a
`New case` link to `INPUT_UI_URL` (`cfna/config.py`, default port 8765, `--port` to change).
Tests: `tests/test_serve.py` (25 cases — markup balance, escaping, static/health/API, the
analyze flow, validation, and path-traversal blocking).

## Report template

Layout sourced from TemplateMo 602 "Graph Page" (https://templatemo.com/tm-602-graph-page),
free for commercial use. `cfna/report/assets/graph-page.css` is the unmodified template sheet;
`cfna/report/assets/cfna.css` is our layer on top (chips, verdict, case file, tree, graph chrome,
tables). `render_html()` emits the template's section skeleton and injects case data; both sheets
are inlined so `report.html` works from `file://`.

## Fixed along the way

- `find_spans` accepted candidates in priority order, so a later high-priority span could reject an
  earlier non-overlapping one (accounts/phones/IMEIs silently dropped from mixed sentences). Now
  position-ordered with priority used only to resolve true overlaps.
- `NAME_AFTER_RE`/`DISTRICT_RE` markers were case-sensitive; "Victim Sourav Banerjee" never matched.
  Markers now use scoped `(?i:...)` while the name group stays case-sensitive.
- Role labelling: a line saying "victim funds" mislabelled mule accounts as victims → victims rule
  now requires zero inflow; recruiters no longer overwrite pass-through mules; assignment order is
  victim → recruiter → mule → operator → kingpin.
- Evidence `sim_swap_table` now groups by **MSISDN with ≥2 SIMs** (re-issue history), not ICCID →
  MSISDNs.
- Trial scoring restricts predictions to the entity types present in `truth.json`.
- Role markers were applied to **every** entity in a sentence, so one pasted paragraph labelled the
  kingpin a victim. Markers are now resolved per sentence to the entity they introduce (forward
  window, tight backward window for trailing mentions like "… before the kingpin"), then carried
  **down** `owns` edges to the account/number the owner controls — never back up, and never over a
  different role already on the target (two people sharing one MSISDN must not smear labels).
- `Kingpin X holds account Y` produced no edge at all in narrative input, so the account stayed
  roleless: possession verbs now create `owns` links.
- Narrative-only input reported "victim loss Rs.0": loss statements (`X lost Rs.N`) are stored as
  `loss_amount` on the subject and surfaced through `NodeMetrics.loss_amount` in the FIR, evidence
  and Bob summaries.
- Hierarchy precedence: a node carrying a kingpin/operator/recruiter/mule label can no longer be
  demoted to victim (or a kingpin to mule) by a second marker in the same text.
- SIM-swap keyword list gained the narrative phrasings actually used in complaints
  (`reissued`, `sim hijack`, `duplicate sim`, …) — a pasted "SIM was reissued + OTP read" note now
  classifies as `SIM_SWAP_OTP` instead of tying with `PHISH_VISH`.

## Bob / coin budget

- `cfna/bob/`: `BOB_BACKEND="local"` (default), `IBM_BOB_ENDPOINT = None`.
- External calls so far: **0**. Coins spent: **0**. The hook is ready when the IBM Bob endpoint and
  coin allowance are provided.

## Future work (not started)

- LP/ML scoring layer behind the existing Bob hook (needs endpoint + coins).
- Geo clustering of IP/device sessions; graph export to GraphML.
- More trial cases (loan-app, romance, card cloning) to lift pattern coverage beyond 3/9.

# CFNA — Cyber Fraud Network Analyzer (Bob-powered)

A deterministic, offline Python tool that turns raw cyber-fraud material (transaction CSVs, call
CDRs, SIM/device registries, device sessions and free-text notes/complaints/statement transcripts)
into an analysed case: extracted entities, a money/call/device network, a classified fraud pattern,
an organisational hierarchy (kingpin → operator → recruiter → mule → victim), a risk ranking, an
evidence pack, an FIR-ready case brief and an interactive HTML network report.

No LLM is required. All extraction and classification is rule/regex based, so every claim in the
report is traceable to a source line or CSV row. An optional "Bob" reasoning backend is wired in as
a pluggable layer (see [Bob integration](#bob-integration)).

## Requirements

- Python 3.10+ (tested on 3.14)
- Standard library only — nothing to `pip install`.

## Install / run

```powershell
cd bob-ai-hackathon-cipher-matrix\src
python -m cfna --help          # works without installing anything
python -m cfna                 # no subcommand = start the input form (browser opens itself)
start_cfna.bat                 # same thing, double-clickable from Explorer (Ctrl+C stops it)
# optional: pip install -e .   ->   adds a `cfna` launcher to your Scripts dir
#                                  (add that dir to PATH, or keep using `python -m cfna`)
```

To just open the tool: double-click **`start_cfna.bat`**, or run `python -m cfna`. Either way the
form appears at `http://127.0.0.1:8765/`, you paste your case, submit, and the report opens —
no flags, no console commands. Everything below is for when you *do* want the CLI.

## Quick start

```powershell
# 1. Generate the three mock trial cases + ground truth
python -m cfna.datagen

# 2. Score pattern accuracy and role F1 against ground truth (exit 0 = all pass)
python -m cfna trial -v

# 3. Analyse one case and write the outputs
python -m cfna run data/cases/jamtara_sim_swap -o output

# 4. Batch-analyse every case under data/cases
python -m cfna batch data/cases -o output

# 5. Look at the result
start output\jamtara_sim_swap\report.html
```

(Or skip the CLI entirely: `start_cfna.bat` → paste → submit → report.)

### Analyse your own material

The tool is not tied to the bundled cases — feed it your own text, files or a live paste:

```powershell
# a) browser input form - no CLI flags to remember (localhost only, stdlib server)
python -m cfna                  # or: python -m cfna serve   (or double-click start_cfna.bat)
#    opens http://127.0.0.1:8765/ : paste notes + a CSV/JSON table (or load a file),
#    submit, and the report opens at http://127.0.0.1:8765/report/<case_id>/report.html
#    stop it with Ctrl+C; --port/--dest/-o/--no-browser change where things go

# b) write example input files you can edit, then hand them back
python -m cfna template .
python -m cfna new --title "My case" --file cfna_input_template\incident_notes.txt --file cfna_input_template\transactions.csv

# c) flags only (non-interactive, scriptable)
python -m cfna new --id my_case --title "My case" --district Jamtara --text "Victim lost Rs.64000 after the OTP was read." --file C:\intel\cdr.csv -o output

# d) pipe notes straight from another command / editor
Get-Content complaint.txt | python -m cfna new --title "Complaint" -o output

# e) interactive wizard: prompts for case metadata, file paths, a pasted note and a pasted table
python -m cfna new

# f) a single bare file also works — run wraps it into a case automatically
python -m cfna run C:\intel\statement.txt -o output
```

`cfna new` writes a normal case directory under `data/cases/<case_id>/` (or `--dest`), so everything
else — `run`, `batch`, `list` — works on it unchanged. `--no-run` creates the folder only,
`--force` adds files to an existing case, `--stdin-format csv` treats piped input as a table, and
`--text`/`--text-file`/`--file`/`--table` are all repeatable.

`cfna serve` writes to `data/web_cases/` instead (so `batch`/`trial` over `data/cases` are never
disturbed), re-analyses whenever you re-submit the same case id, and refuses to touch a bundled
trial case. Every report's nav carries a **New case** link back to that form.

Outputs per case (written to `<out>/<case_id>/`):

| File | Contents |
| --- | --- |
| `report.html` | Interactive report: TemplateMo "Graph Page" layout — hero case file, stat cards, charts, vis-network graph, hierarchy, evidence annexures, FIR actions |
| `fir_brief.md` | 12-section FIR draft: facts, modus operandi, hierarchy, evidence annexures, legal sections, recommended actions |
| `case_data.json` | Full machine-readable case + brief |
| `network.json` | `{nodes, edges}` with roles and risk scores for external visualisation |

`report.html` is fully self-contained (CSS inlined, no build step, no server). The only network
request it makes is the vis-network script from unpkg; open it straight from disk with
`start output\<case>\report.html`.

## Report design

The report layout is based on
**[TemplateMo 602 – Graph Page](https://templatemo.com/tm-602-graph-page)** (free for commercial
use). Two CSS files ship in the package and are inlined into every report:

| File | Purpose |
| --- | --- |
| `cfna/report/assets/graph-page.css` | TemplateMo's design system — dark cyberpunk palette (`#0a0e27`, `#00ffcc`, `#ff6b6b`), nav, hero, stat cards, metrics, chart cards, footer |
| `cfna/report/assets/cfna.css` | Our layer — chips, verdict banner, case-file panel, hierarchy tree, graph toolbar/detail/legend, tables, responsive tweaks |

`cfna/report/html_report.py` emits the template's markup skeleton and fills it with case data:

```
nav        → CFNA logo + 7 anchor links (Home / Dashboard / Analytics / Network / Hierarchy / Evidence / FIR)
             + "New case" -> the local input form (http://127.0.0.1:8765/)
hero       → case title, meta chips, pattern verdict + confidence bar, "case file snapshot" panel
dashboard  → 6 stat cards (money trail, entities, links, victims, mules, kingpins) + 6 metric tiles
analytics  → 4 bar charts (role distribution, pattern confidence, largest transfers, top risk) + signals list
network    → toolbar with role filters + search, vis-network canvas, node detail panel, legend
hierarchy  → monospace tree (kingpin → tiers → victims) + Bob's observations / intelligence gaps
evidence   → 7 annexure tables (freeze list, victims, SIM swap, devices, calls, transfers, timeline)
fir        → recommended actions, sections of law, outputs and provenance
footer     → attribution to TemplateMo
```

## Input layout

A case is a directory of loosely-named files. CSV kind is inferred from the header, free text from
the extension — you do not have to use our filenames. `cfna new` builds this directory for you from
whatever you supply (flags, pipe, or the wizard), and `cfna template` writes a fillable example.

```
data/cases/<case_id>/
  case.json                   # metadata: title, PS, district, dates, officer
  01_incident_notes.txt        # any .txt/.md — narrative intelligence
  02_transactions.csv          # header containing: from_account/from_upi/to_account/to_upi/amount_inr/timestamp/remarks
  03_call_logs.csv             # msisdn_a/msisdn_b/duration_sec/cell_id/imei_a/imei_b/timestamp
  04_sim_device_registry.csv   # msisdn/iccid/imei/activation_date/status/provider/owner_name/remarks
  05_device_sessions.csv       # imei/msisdn/ip_address/app_version/latitude/longitude/timestamp
  06_victim_complaints.txt     # free text
  07_accused_statements.txt    # free text
  truth.json                   # (trial only) expected pattern + kingpin/mule/victim node IDs
```

Recognised transaction aliases include `payer_account`/`payee_vpa`/`src_upi`/`dst_upi`, so bank and
wallet exports drop in directly. Rows with unknown headers are ingested generically: identifiers are
still extracted and co-occurrence linked.

## What the pipeline does

1. **Ingest** — `load_case_dir` reads CSVs/txt/json into `Document`s and record rows.
2. **Extract** — priority-ordered span arbitration over email, UPI VPA, ICCID, IMEI, PAN, Aadhaar,
   card, IFSC, phone, vehicle, IP, handle and account regexes; person names after role markers;
   structured rows become typed entities with `transfer`, `call`, `sim_bound_to_msisdn`,
   `device_used_sim/msisdn`, `owns`, `maps_to`, `session_ip`, `located_at` edges.
3. **Text relations** — sentence-level explicit links (`linked to`, `belonging to`, `operated by`…),
   transfer edges (transfer verb + amount + ≥2 identifiers), possession edges
   (`Anup Saha holds account 5001…` → `owns`), loss statements (`X lost Rs.N` → `loss_amount`
   on the subject), co-occurrence fallback. Role markers are resolved **per sentence and to the
   entity they name** — "Kingpin Anup Saha … victim Ramesh Kumar" labels each actor, not both —
   and then flow down `owns` edges to the account/number the owner controls.
4. **Metrics** — per-node in/out amounts, pass-through ratio, narrative-stated loss, PageRank,
   Brandes betweenness, label-propagation communities, flow vs call in/out degrees (kept separate
   so a victim is never mistaken for a collector).
5. **Pattern classification** — 9 patterns scored as
   `0.55 × keyword + 0.45 × structural` (weights per pattern, some keyword- or structure-heavy):
   `SIM_SWAP_OTP`, `MULE_CHAIN`, `TASK_INVESTMENT_SCAM`, `PHISH_VISH`, `LOAN_APP_EXTORTION`,
   `IDENTITY_KYC_FRAUD`, `CARD_CLONING`, `SEXTORTION`, `ROMANCE_HONEYTRAP`.
   `python -m cfna patterns` prints every pattern with its keywords and legal sections.
6. **Hierarchy** — victims (loss-only nodes), pass-through mules (≥₹5k in, ≥85% forwarded),
   operators (multi-SIM/multi-device or labelled), recruiters (labelled or ≥3 mule links),
   kingpins (terminal high-inflow beneficiaries); mule tiers by reverse hop distance from the kingpin.
7. **Risk** — role weight + inflow/outflow share + betweenness + device/SIM diversity, 0–99 scale.
8. **Timeline / evidence / Bob** — timestamped events, transfer & call annexures, SIM-swap binding
   table (MSISDN with ≥2 ICCIDs), device table, victim loss table, freeze list, investigation gaps.
9. **Report** — `render_fir` (markdown) and `render_html` (TemplateMo layout, CSS inlined,
   vis-network from CDN).

## How it runs (code path)

```python
from pathlib import Path
from cfna.pipeline import build_case, analyze, export_outputs

# 1. read the case directory (CSV kind is sniffed from the header, text from the extension)
case, _ = build_case(Path("data/cases/jamtara_sim_swap"))

# 2. extract -> metrics -> pattern -> roles -> risk -> timeline -> evidence -> Bob
brief, metrics, evidence = analyze(case)

print(brief.primary.id, round(brief.primary.score, 2))     # SIM_SWAP_OTP 1.0
print(brief.hierarchy["kingpin"])                          # ['account:5001000000001', ...]

# 3. write report.html / fir_brief.md / case_data.json / network.json
export_outputs(case, brief, metrics, evidence, Path("output") / case.meta.case_id)
```

Everything above is what `python -m cfna run <case_dir> -o output` does, wrapped in the CLI. The
same pipeline backs `cfna batch` (all cases) and `cfna trial` (score against `truth.json`).

## Trial / evaluation

`truth.json` per case:

```json
{
  "expected_primary": ["SIM_SWAP_OTP"],
  "kingpins": ["account:5001000000001"],
  "mules": ["account:5001000020001", "account:5001000030001"],
  "victims": ["account:5001000010001"],
  "min_pattern_confidence": 0.5,
  "thresholds": {"kingpin_f1": 1.0, "mule_f1": 0.8, "victim_f1": 0.9}
}
```

Node IDs are `<type>:<value>` (e.g. `account:…`, `phone:…`, `device:…`). Predictions are compared
only against the entity types present in the truth file, then precision/recall/F1 are computed per
role. `cfna trial` prints a table and exits `0` only when every case passes its thresholds — usable
directly as a CI gate.

Current state: **3/3 cases PASS — pattern 3/3, kingpin F1 1.00, mule F1 1.00, victim F1 1.00.**

## Mock cases

| Case | Pattern | Shape |
| --- | --- | --- |
| `jamtara_sim_swap` | `SIM_SWAP_OTP` | 6 victims → 4 entry mules → 3 layer → 2 → cashout; 4 victim MSISDNs re-issued onto syndicate SIMs/devices |
| `ranchi_fake_task_app` | `TASK_INVESTMENT_SCAM` | 8 victims → 4 collectors → 2 layers → kingpin (UPI-only cashout) |
| `kolkata_vishing_blast` | `PHISH_VISH` | 9 victims ← broadcast VoIP caller → 3 beneficiaries → 1 layer → cashout |

Regenerate at any time with `python -m cfna.datagen` (seeded, byte-identical output).

## Tests

```powershell
python -m unittest discover -s tests -v
```

76 tests (in 7 test files): span extraction & overlap arbitration, role-marker labels, text transfer edges, keyword
and structural pattern detectors, synthetic hierarchy rules, trial-data role checks, end-to-end
export/trial verification, report validation (template structure, inlined CSS, tag balance,
`node --check` on the generated JavaScript), the intake layer (slugify, table sniffing, case
writing round-trip, the `new`/`template`/`run <file>` commands, piped stdin, wizard prompts) and
the web input form (`tests/test_serve.py`: form markup balance, escaped errors, static assets,
health/API endpoints, the analyze → 303 → report flow, empty/trial-case rejection, path-traversal
blocking on `/report/`, and the bare `python -m cfna` → serve default).

## Bob integration

Bob is the analysis assistant. Today it runs locally as deterministic heuristics (`cfna/bob/`):
pattern verdict, secondary-pattern note, network shape, hierarchy summary, evidence gaps and
recommended next actions. To point it at the IBM Bob service later:

```python
from cfna.bob import IBM_BOB_ENDPOINT, BOB_BACKEND
# set IBM_BOB_ENDPOINT = "https://.../v1/reason" and BOB_BACKEND = "ibm"
```

`BobAgent.reason()` posts the analysed case summary there and falls back to the local heuristics if
the endpoint is unset (the current default: **0 coins consumed, 0 external calls**).

## Project layout

```
cfna/
  cli.py            run / new / template / batch / trial / list / patterns / serve
  intake.py         user input -> case directory (flags, pipe, wizard, template, single file)
  serve.py          localhost input form: stdlib HTTP server (form -> intake -> report)
  pipeline.py       build_case -> analyze -> export_outputs
  config.py         regexes, PSP list, role markers, legal sections, per-pattern actions,
                    INPUT_UI_URL (where the input form lives)
  models.py         Entity / Relation / CaseGraph / CaseBrief / assessments
  graph.py          DiGraph: PageRank, Brandes, communities, hops (stdlib only)
  ingest/loaders.py CSV + text + case.json loading, header-based kind detection
  extract/          entity spans, structured ingestion, text relations
  analysis/         metrics, patterns, hierarchy, risk, timeline, evidence
  bob/              pluggable reasoning layer (local heuristics + IBM endpoint hook)
  report/           fir.py (markdown), html_report.py (report renderer)
    assets/         graph-page.css (TemplateMo 602), cfna.css (our layer)
  datagen.py        seeded mock-data generator (helpers + case 1)
  datagen_cases.py  cases 2 and 3 + generate_all
tests/              unittest suite (incl. test_intake.py for the user-input commands,
                    test_serve.py for the browser input form)
start_cfna.bat      double-click entry point -> `python -m cfna serve`
data/cases/         generated trial cases with truth.json
output/             generated reports
```

## Legal mapping (drafted into every FIR brief)

Each pattern maps to a fixed, reviewable section set — e.g. `SIM_SWAP_OTP` → BNS s.318(4)
cheating by impersonation, IT Act s.66D, TRAI/Indian Telecom regulations; `MULE_CHAIN` → BNS s.318
+ PMLA s.3 with a Section 65/66A freeze request; `TASK_INVESTMENT_SCAM` → BNS s.318 + IT Act
s.66C/66D. Sections are drafting aids and must be verified by the IO before filing.

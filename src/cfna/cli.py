from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from cfna import __version__
from cfna import config as cfg
from cfna.intake import case_dir_for, ensure_case, intake_from_flags, wizard, write_case, write_template
from cfna.models import ROLE_ORDER, CaseGraph
from cfna.pipeline import analyze, build_case, export_outputs, run_case

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = ROOT / "data" / "cases"
DEFAULT_OUT = ROOT / "output"


def _print_summary(case: CaseGraph, brief: Any, evidence: dict[str, list[dict]]) -> None:
    pattern = brief.primary
    print(f"\n=== {case.meta.title} [{case.meta.case_id}] ===")
    if pattern:
        print(f"Pattern : {pattern.name} (confidence {int(pattern.score * 100)}%)")
        for signal in pattern.signals[:3]:
            print(f"   - {signal}")
    counts = brief.stats.get("role_counts", {})
    print("Roles   : " + ", ".join(f"{role}={counts.get(role, 0)}" for role in ROLE_ORDER if role in counts))
    print(f"Graph   : {brief.stats.get('entities')} entities, {brief.stats.get('relations')} relations, "
          f"trail Rs.{brief.stats.get('total_trail_amount', 0):,.0f}")
    kingpins = brief.hierarchy.get("kingpin", [])
    if kingpins:
        print("Kingpin : " + ", ".join(k.split(":", 1)[1] for k in kingpins[:3]))
    top = sorted(brief.assessments.values(), key=lambda a: -a.risk)[:5]
    print("Top risk: " + "; ".join(f"{a.node_id.split(':', 1)[1][:18]}({a.role},{a.risk})" for a in top))
    print("Bob     :")
    for insight in brief.insights[:4]:
        print(f"   * {insight}")
    if brief.gaps:
        print("Gaps    :")
        for gap in brief.gaps[:3]:
            print(f"   ! {gap}")
    freeze = [r for r in evidence.get("accounts_freeze_list", []) if r["freeze"]]
    print(f"Freeze  : {len(freeze)} account(s) recommended for freezing")
    print("")


def cmd_run(args: argparse.Namespace) -> int:
    target = Path(args.case)
    try:
        case_dir = ensure_case(target)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if case_dir != target:
        print(f"input file wrapped as case: {case_dir}")
    out_root = Path(args.out) if args.out else DEFAULT_OUT
    result = run_case(case_dir, out_root)
    _print_summary(result["case"], result["brief"], result["evidence"])
    print("Outputs:")
    for name, path in result["outputs"].items():
        print(f"   {path}")
    return 0


def cmd_new(args: argparse.Namespace) -> int:
    from cfna.intake import read_stdin, slugify

    dest = Path(args.dest)

    # Piped stdin is only read when it is the intended source: either --stdin was passed or no
    # other payload flag was, so `echo "notes" | cfna new --title x` works while
    # `cfna new --file a.txt < script` never blocks on a pipe it does not need.
    has_payload = any([args.text, args.text_file, args.file, args.table])
    wants_stdin = args.stdin or not has_payload
    piped = read_stdin(sys.stdin) if (wants_stdin and not sys.stdin.isatty()) else ""

    intake = intake_from_flags(args)
    if piped.strip():
        if args.stdin_format == "csv":
            intake.tables.append(("stdin_records.csv", piped))
        else:
            intake.texts.append(("stdin_notes", piped))

    if not intake.has_input():
        if not sys.stdin.isatty():
            print(
                "error: no input given. Pass --text/--text-file/--file/--table, "
                "pipe notes on stdin, or run in an interactive terminal.",
                file=sys.stderr,
            )
            return 2
        print("No input supplied - starting the interactive intake wizard.\n")
        intake = wizard()

    if not intake.meta.get("title"):
        intake.meta["title"] = args.title or "Untitled Cyber Fraud Case"
    if args.title:
        intake.meta["title"] = args.title
    if args.case_id:
        intake.meta["case_id"] = args.case_id
    if not intake.meta.get("case_id"):
        intake.meta["case_id"] = slugify(intake.meta["title"])

    if not intake.has_input():
        print(
            "error: nothing to analyze - give narrative text, a table, or at least one intel file",
            file=sys.stderr,
        )
        return 2

    try:
        case_dir = case_dir_for(intake.meta, dest, force=args.force)
    except FileExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    written = write_case(
        case_dir, intake.meta, intake.texts, intake.tables, intake.files, force=args.force
    )
    print(f"case created: {written}")
    for path in sorted(p for p in written.iterdir() if p.is_file()):
        print(f"   {path.name}")

    if args.no_run:
        print(f"\nnext: python -m cfna run \"{written}\" -o {DEFAULT_OUT}")
        return 0

    out_root = Path(args.out) if args.out else DEFAULT_OUT
    result = run_case(written, out_root)
    _print_summary(result["case"], result["brief"], result["evidence"])
    print("Outputs:")
    for name, path in result["outputs"].items():
        print(f"   {path}")
    return 0


def cmd_template(args: argparse.Namespace) -> int:
    target = write_template(Path(args.dir))
    print(f"input template written to {target}")
    for path in sorted(target.iterdir()):
        print(f"   {path.name}")
    print(f"\nedit the files, then e.g.\n   python -m cfna new --title \"My case\" "
          f"--file {target / 'incident_notes.txt'} --file {target / 'transactions.csv'}")
    return 0


def cmd_batch(args: argparse.Namespace) -> int:
    root = Path(args.cases)
    case_dirs = sorted(p for p in root.iterdir() if p.is_dir()) if root.is_dir() else []
    if not case_dirs:
        print(f"error: no cases under {root}", file=sys.stderr)
        return 2
    out_root = Path(args.out) if args.out else DEFAULT_OUT
    failures = 0
    for case_dir in case_dirs:
        try:
            result = run_case(case_dir, out_root)
        except Exception as exc:  # noqa: BLE001
            print(f"[FAIL] {case_dir.name}: {exc}")
            failures += 1
            continue
        brief = result["brief"]
        pattern = brief.primary
        label = f"{pattern.name} {int(pattern.score * 100)}%" if pattern else "none"
        print(f"[ok] {case_dir.name}: pattern={label}, out={result['out_dir']}")
    return 1 if failures else 0


def _f1(predicted: set[str], truth: set[str]) -> tuple[float, float, float]:
    if not truth and not predicted:
        return 1.0, 1.0, 1.0
    if not predicted or not truth:
        return 0.0, 0.0, 0.0
    tp = len(predicted & truth)
    precision = tp / len(predicted)
    recall = tp / len(truth)
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return f1, precision, recall


def cmd_trial(args: argparse.Namespace) -> int:
    root = Path(args.cases)
    case_dirs = sorted(
        p for p in root.iterdir()
        if p.is_dir() and (p / "truth.json").exists()
    ) if root.is_dir() else []
    if not case_dirs:
        print(f"error: no trial cases with truth.json under {root}", file=sys.stderr)
        return 2

    rows: list[dict[str, Any]] = []
    all_pass = True
    for case_dir in case_dirs:
        truth = json.loads((case_dir / "truth.json").read_text(encoding="utf-8"))
        case, _ = build_case(case_dir)
        brief, metrics, evidence = analyze(case)
        primary = brief.primary
        expected = truth.get("expected_primary") or truth.get("expected_patterns") or []
        if isinstance(expected, str):
            expected = [expected]
        pattern_ok = bool(primary and primary.id in expected)
        conf_ok = (primary.score >= float(truth.get("min_pattern_confidence", 0.35))) if primary else False

        predicted_roles: dict[str, set[str]] = {"kingpin": set(), "mule": set(), "victim": set()}
        for node, assessment in brief.assessments.items():
            if assessment.role in predicted_roles:
                predicted_roles[assessment.role].add(node)

        scores = {}
        truth_types: set[str] = set()
        for role in ("kingpin", "mule", "victim"):
            for item in (truth.get(f"{role}s", truth.get(role, [])) or []):
                if ":" in str(item):
                    truth_types.add(str(item).split(":", 1)[0])
        for role in ("kingpin", "mule", "victim"):
            truth_set = set(truth.get(f"{role}s", truth.get(role, [])) or [])
            restricted = {
                node for node in predicted_roles[role]
                if ":" not in node or node.split(":", 1)[0] in truth_types
            }
            f1, precision, recall = _f1(restricted, truth_set)
            scores[role] = {"f1": f1, "precision": precision, "recall": recall,
                            "predicted": len(restricted), "truth": len(truth_set)}

        thresholds = truth.get("thresholds", {})
        passed = (
            pattern_ok
            and conf_ok
            and scores["kingpin"]["f1"] >= thresholds.get("kingpin_f1", 0.5)
            and scores["mule"]["f1"] >= thresholds.get("mule_f1", 0.6)
            and scores["victim"]["f1"] >= thresholds.get("victim_f1", 0.7)
        )
        all_pass = all_pass and passed
        rows.append(
            {
                "case": case_dir.name,
                "pattern": f"{primary.id} {primary.score:.2f}" if primary else "none",
                "expected": ",".join(expected),
                "pattern_ok": pattern_ok and conf_ok,
                "kingpin_f1": scores["kingpin"]["f1"],
                "mule_f1": scores["mule"]["f1"],
                "victim_f1": scores["victim"]["f1"],
                "passed": passed,
            }
        )
        if args.verbose:
            print(f"\n--- {case_dir.name} ---")
            for role, data in scores.items():
                print(f"  {role:8s} f1={data['f1']:.2f} p={data['precision']:.2f} r={data['recall']:.2f} "
                      f"(predicted {data['predicted']}, truth {data['truth']})")
            if not pattern_ok and primary:
                missing = set(expected) - {primary.id}
                print(f"  pattern mismatch: got {primary.id}, expected {sorted(missing)}")
                for alt in brief.patterns[1:4]:
                    print(f"    alt: {alt.id} {alt.score:.2f}")

    header = f"{'case':34s} {'pattern':28s} {'expect':24s} {'pat':4s} {'kingF1':7s} {'muleF1':7s} {'vicF1':7s} {'result':7s}"
    print("\n" + header)
    print("-" * len(header))
    for row in rows:
        print(
            f"{row['case'][:34]:34s} {row['pattern'][:28]:28s} {row['expected'][:24]:24s} "
            f"{'PASS' if row['pattern_ok'] else 'FAIL':4s} {row['kingpin_f1']:7.2f} {row['mule_f1']:7.2f} "
            f"{row['victim_f1']:7.2f} {'PASS' if row['passed'] else 'FAIL':7s}"
        )
    total = len(rows)
    passed = sum(1 for r in rows if r["passed"])
    pat_passed = sum(1 for r in rows if r["pattern_ok"])
    avg = {role: sum(r[f"{role}_f1"] for r in rows) / total for role in ("kingpin", "mule", "victim")}
    print("-" * len(header))
    print(f"pattern accuracy: {pat_passed}/{total} ({100 * pat_passed / total:.0f}%)  "
          f"role F1: kingpin={avg['kingpin']:.2f} mule={avg['mule']:.2f} victim={avg['victim']:.2f}  "
          f"OVERALL: {passed}/{total} {'PASS' if all_pass else 'FAIL'}")
    print("")
    return 0 if all_pass else 1


def cmd_serve(args: argparse.Namespace) -> int:
    from cfna.serve import serve

    return serve(
        host=args.host,
        port=args.port,
        dest=Path(args.dest),
        out=Path(args.out) if args.out else DEFAULT_OUT,
        open_browser=not args.no_browser,
    )


def cmd_patterns(args: argparse.Namespace) -> int:
    from cfna.analysis.patterns import KEYWORDS

    print("Registered fraud patterns (keyword + structural detectors):\n")
    for pid in cfg.PATTERN_ORDER:
        print(f"  {pid}")
        print(f"      {cfg.PATTERN_SUMMARY[pid]}")
        print(f"      keywords: {', '.join(KEYWORDS[pid][:6])}")
        print(f"      sections: {cfg.LEGAL_BY_PATTERN[pid][0]}")
        print("")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    root = Path(args.cases)
    if not root.is_dir():
        print(f"no cases at {root}")
        return 1
    for case_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        files = sorted(f.name for f in case_dir.iterdir() if f.is_file())
        truth = " [trial+truth]" if (case_dir / "truth.json").exists() else ""
        print(f"  {case_dir.name}{truth}: {', '.join(files)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cfna",
        description="CFNA - Bob-powered Cyber Fraud Network Analyzer: unstructured intel to FIR-ready brief",
    )
    parser.add_argument("--version", action="version", version=f"cfna {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser(
        "run",
        help="analyze a case directory (or a single txt/csv/json intel file) and write reports",
    )
    run.add_argument("case", help="path to a case directory, or a single intel file")
    run.add_argument("-o", "--out", help="output root directory (default: ./output)")
    run.set_defaults(func=cmd_run)

    new = sub.add_parser(
        "new",
        help="create a case from your own input: files, pasted text, piped stdin, or an interactive wizard",
    )
    new.add_argument("--title", help="case title")
    new.add_argument("--id", dest="case_id", help="case id / folder name (default: slug of the title)")
    new.add_argument("--ps", help="police station")
    new.add_argument("--district", help="district")
    new.add_argument("--state", help="state")
    new.add_argument("--complainant", help="complainant name")
    new.add_argument("--occurred", help="date of occurrence (YYYY-MM-DD)")
    new.add_argument("--reported", help="date of reporting (YYYY-MM-DD)")
    new.add_argument("--officer", help="investigating officer")
    new.add_argument("--notes", help="short case remarks")
    new.add_argument("--text", action="append", help="narrative text (repeatable)")
    new.add_argument("--text-file", action="append", help="narrative file to copy in (repeatable)")
    new.add_argument("--file", action="append", help="any intel file: csv/json/txt (repeatable)")
    new.add_argument("--table", action="append", help="CSV/TSV file to ingest as a table (repeatable)")
    new.add_argument("--stdin", action="store_true", help="read narrative (or a table) from stdin")
    new.add_argument("--stdin-format", choices=["text", "csv"], default="text",
                     help="how to interpret piped stdin (default: text)")
    new.add_argument("--dest", default=str(DEFAULT_DATA), help="where to create the case (default: data/cases)")
    new.add_argument("--out", "-o", help="output root directory for the report (default: ./output)")
    new.add_argument("--force", action="store_true", help="add files to an existing case directory")
    new.add_argument("--no-run", action="store_true", help="create the case folder only, do not analyze")
    new.set_defaults(func=cmd_new)

    tmpl = sub.add_parser("template", help="write example input files you can edit and hand back")
    tmpl.add_argument("dir", nargs="?", default=".", help="destination folder (default: .)")
    tmpl.set_defaults(func=cmd_template)

    batch = sub.add_parser("batch", help="analyze every case under a directory")
    batch.add_argument("cases", nargs="?", default=str(DEFAULT_DATA), help="cases root (default: data/cases)")
    batch.add_argument("-o", "--out", help="output root directory (default: ./output)")
    batch.set_defaults(func=cmd_batch)

    trial = sub.add_parser("trial", help="run trial datasets against ground truth and score accuracy")
    trial.add_argument("cases", nargs="?", default=str(DEFAULT_DATA), help="cases root containing truth.json files")
    trial.add_argument("-v", "--verbose", action="store_true", help="show per-role confusion detail")
    trial.set_defaults(func=cmd_trial)

    listing = sub.add_parser("list", help="list available case datasets")
    listing.add_argument("cases", nargs="?", default=str(DEFAULT_DATA))
    listing.set_defaults(func=cmd_list)

    pats = sub.add_parser("patterns", help="list detectable fraud pattern signatures")
    pats.set_defaults(func=cmd_patterns)

    serve_p = sub.add_parser(
        "serve",
        help="open a localhost input form in the browser (paste your own case, no CLI needed)",
    )
    serve_p.add_argument("--host", default=cfg.INPUT_UI_HOST,
                         help=f"bind address (default: {cfg.INPUT_UI_HOST})")
    serve_p.add_argument("--port", type=int, default=cfg.INPUT_UI_PORT,
                         help=f"port (default: {cfg.INPUT_UI_PORT})")
    serve_p.add_argument("--dest", default=str(ROOT / cfg.DEFAULT_WEB_CASES_SUBDIR),
                         help=f"where web cases are stored (default: {cfg.DEFAULT_WEB_CASES_SUBDIR})")
    serve_p.add_argument("-o", "--out", help="output root directory for reports (default: ./output)")
    serve_p.add_argument("--no-browser", action="store_true", help="do not auto-open a browser tab")
    serve_p.set_defaults(func=cmd_serve)
    return parser


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    if not raw:
        # bare `python -m cfna` opens the local input form - no subcommand to remember.
        raw = ["serve"]
    parser = build_parser()
    args = parser.parse_args(raw)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

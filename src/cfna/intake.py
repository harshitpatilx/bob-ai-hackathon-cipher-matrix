"""User input intake: turn files, pasted text, pasted tables or stdin into a case directory.

The analyzer never reads "special" input formats — anything the intake writes into a case
directory is picked up by `cfna.ingest.load_case_dir`, which sniffs CSV kinds from the header
and treats `.txt/.md/.log/.statement` as narrative. That means a user can hand us:

* a narrative note (typed or pasted)
* one or more CSV/JSON exports (bank statement, CDR, SIM registry, device log)
* a pasted CSV table (header + rows)
* any mixture of the above

and get the same report the mock trial cases produce.
"""
from __future__ import annotations

import csv
import io
import json
import re
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from cfna.models import CaseMeta

TEXT_SUFFIXES = {".txt", ".md", ".log", ".statement"}
CASE_FILE_NAMES = {"case.json", "meta.json", "case_meta.json"}

META_FIELDS: list[tuple[str, str]] = [
    ("title", "Case title"),
    ("case_id", "Case id (folder name)"),
    ("police_station", "Police station"),
    ("district", "District"),
    ("state", "State"),
    ("complainant", "Complainant"),
    ("occurred_on", "Date of occurrence (YYYY-MM-DD)"),
    ("reported_on", "Date of reporting (YYYY-MM-DD)"),
    ("officer", "Investigating officer"),
    ("notes", "Notes / remarks"),
]

CSV_END = "END"
TEXT_END = "."


@dataclass
class Intake:
    """Everything a user handed us, before it hits the filesystem."""

    meta: dict[str, str] = field(default_factory=dict)
    texts: list[tuple[str, str]] = field(default_factory=list)   # (suggested name, body)
    tables: list[tuple[str, str]] = field(default_factory=list)  # (file name, csv body)
    files: list[Path] = field(default_factory=list)              # copied verbatim

    def has_input(self) -> bool:
        return bool(self.texts or self.tables or self.files)

    def merge(self, other: "Intake") -> "Intake":
        self.meta.update({k: v for k, v in other.meta.items() if v})
        self.texts.extend(other.texts)
        self.tables.extend(other.tables)
        self.files.extend(other.files)
        return self


def slugify(text: str, fallback: str = "case") -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.strip().lower()).strip("_")
    return slug[:60] or fallback


def sniff_table(text: str) -> tuple[list[str], list[list[str]]]:
    """Parse pasted CSV/TSV text into (header, rows). Comma, tab and pipe are accepted."""
    sample = text.lstrip("\ufeff")
    if not sample.strip():
        return [], []
    try:
        dialect: Any = csv.Sniffer().sniff(sample[:4096], delimiters=",\t|;")
    except csv.Error:
        dialect = csv.excel
    rows = [row for row in csv.reader(io.StringIO(sample), dialect) if any(cell.strip() for cell in row)]
    if not rows:
        return [], []
    header = [cell.strip() for cell in rows[0]]
    body = [[cell.strip() for cell in row] for row in rows[1:]]
    return header, body


def table_to_csv(header: list[str], rows: Iterable[list[str]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _next_prefix(case_dir: Path) -> int:
    used = 0
    for path in case_dir.iterdir() if case_dir.is_dir() else []:
        match = re.match(r"^(\d+)_", path.name)
        if match:
            used = max(used, int(match.group(1)))
    return used + 1


def write_case(
    case_dir: Path,
    meta: dict[str, str],
    texts: list[tuple[str, str]],
    tables: list[tuple[str, str]],
    files: list[Path],
    force: bool = False,
) -> Path:
    """Materialise an intake as a case directory the analyzer already understands."""
    if case_dir.exists() and any(case_dir.iterdir()) and not force:
        raise FileExistsError(f"{case_dir} already exists (use force to add to it)")
    case_dir.mkdir(parents=True, exist_ok=True)

    payload = {key: value for key, value in meta.items() if value}
    (case_dir / "case.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    counter = _next_prefix(case_dir)
    for name, body in texts:
        if not body.strip():
            continue
        target = case_dir / (name if name.endswith(tuple(TEXT_SUFFIXES)) else f"{name}.txt")
        if not re.match(r"^\d+_", target.name):
            target = case_dir / f"{counter:02d}_{target.name}"
            counter += 1
        target.write_text(body.strip() + "\n", encoding="utf-8")

    for name, body in tables:
        if not body.strip():
            continue
        sample = body.lstrip()
        if sample.startswith("[") or sample.startswith("{"):
            # JSON export (list of objects, or {"records": [...]}) - hand it over untouched.
            target = case_dir / f"{counter:02d}_{slugify(Path(name).stem, 'records')}.json"
            counter += 1
            target.write_text(body.strip() + "\n", encoding="utf-8")
            continue
        header, rows = sniff_table(body)
        if not header:
            continue
        target = case_dir / name
        if not re.match(r"^\d+_", target.name) or not target.name.endswith(".csv"):
            target = case_dir / f"{counter:02d}_{slugify(Path(name).stem, 'records')}.csv"
            counter += 1
        target.write_text(table_to_csv(header, rows), encoding="utf-8")

    for path in files:
        if not path.exists():
            raise FileNotFoundError(f"input file not found: {path}")
        target = case_dir / path.name
        if target.exists() and target.resolve() == path.resolve():
            continue
        shutil.copy2(path, target)

    return case_dir


def case_dir_for(meta: dict[str, str], dest: Path, force: bool = False) -> Path:
    case_id = slugify(meta.get("case_id") or meta.get("title") or "case")
    case_dir = dest / case_id
    if case_dir.exists() and any(case_dir.iterdir()) and not force:
        raise FileExistsError(
            f"{case_dir} already exists — pick a different --id or pass --force to add files to it"
        )
    return case_dir


def ensure_case(path: Path, dest: Path | None = None) -> Path:
    """Accept either a case directory or a single intel file and return a case directory."""
    if path.is_dir():
        return path
    if not path.is_file():
        raise FileNotFoundError(f"no such case or file: {path}")
    base = (dest or path.parent / "_intake") / slugify(path.stem, "case")
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        intake = Intake(
            meta={"title": path.stem.replace("_", " ").replace("-", " ").title(), "case_id": base.name},
            texts=[(path.name, _read_text(path))],
        )
    else:
        intake = Intake(
            meta={"title": path.stem.replace("_", " ").replace("-", " ").title(), "case_id": base.name},
            files=[path],
        )
    return write_case(base, intake.meta, intake.texts, intake.tables, intake.files, force=True)


def read_stdin(stream: Any) -> str:
    data = stream.read()
    return data if isinstance(data, str) else data.decode("utf-8", "replace")


def intake_from_flags(args: Any) -> Intake:
    """Build an Intake from argparse arguments (the non-interactive path)."""
    intake = Intake()
    for attr, key in (
        ("title", "title"),
        ("case_id", "case_id"),
        ("ps", "police_station"),
        ("district", "district"),
        ("state", "state"),
        ("complainant", "complainant"),
        ("occurred", "occurred_on"),
        ("reported", "reported_on"),
        ("officer", "officer"),
        ("notes", "notes"),
    ):
        value = getattr(args, attr, None)
        if value:
            intake.meta[key] = str(value)

    for text in getattr(args, "text", None) or []:
        intake.texts.append(("user_notes", text))
    for name in getattr(args, "text_file", None) or []:
        intake.texts.append((Path(name).name, _read_text(Path(name))))
    for name in getattr(args, "table", None) or []:
        intake.tables.append((Path(name).name, _read_text(Path(name))))
    for name in getattr(args, "file", None) or []:
        intake.files.append(Path(name))
    return intake


def wizard(prompt: Any = input) -> Intake:
    """Interactive intake. `prompt` is injectable so tests can drive it."""
    intake = Intake()

    def ask(label: str, default: str = "") -> str:
        suffix = f" [{default}]" if default else ""
        try:
            raw = prompt(f"  {label}{suffix}: ")
        except (EOFError, KeyboardInterrupt):
            print()
            return default
        return (raw or "").strip() or default

    def read_block(kind: str) -> str:
        """Multi-line paste: terminate with '.' (notes) or 'END' (table)."""
        stop = TEXT_END if kind == "text" else CSV_END
        print(
            f"    paste {kind} and finish with a line containing only '{stop}' "
            f"(or Ctrl-D). Empty first line skips."
        )
        lines: list[str] = []
        try:
            while True:
                line = prompt("")
                if line is None:
                    break
                if not lines and not line.strip():
                    break
                if line.strip() == stop:
                    break
                lines.append(line.rstrip("\n"))
        except (EOFError, KeyboardInterrupt):
            print()
        return "\n".join(lines).strip()

    print("\nCFNA intake — describe the case, then hand over whatever intel you have.\n")
    title = ask("Case title", "Untitled Cyber Fraud Case")
    intake.meta["title"] = title
    intake.meta["case_id"] = ask("Case id (folder name)", slugify(title))
    for key, label in META_FIELDS[2:]:
        value = ask(label)
        if value:
            intake.meta[key] = value

    print("\n  [1] Intel files (CSV/JSON export, call log, SIM registry, notes)")
    print("      comma-separated paths, or blank to skip")
    try:
        raw = prompt("  paths: ").strip()
    except (EOFError, KeyboardInterrupt):
        raw = ""
        print()
    for chunk in raw.split(","):
        chunk = chunk.strip().strip('"').strip("'")
        if chunk:
            intake.files.append(Path(chunk))

    print("\n  [2] Narrative notes (incident notes, victim complaints, accused statements)")
    body = read_block("text")
    if body:
        intake.texts.append(("user_notes", body))

    print("\n  [3] Optional table paste (header row first, comma/tab separated)")
    table = read_block("table")
    if table:
        intake.tables.append(("pasted_records.csv", table))

    return intake


def template_files() -> list[tuple[str, str]]:
    """Example input files written by `cfna template`."""
    notes = """INCIDENT NOTES - sample narrative for CFNA input

KEY FINDING: the victim SIM was reissued after a spoofed KYC update and the ported SIM
was used to read OTPs, after which UPI debits were executed from account 5001000123456
to mule account 5001000987654 and then withdrawn immediately.

Kingpin Anup Saha controls the cashout account 5001000000001. Recruiter Suraj Ekka
sourced the rented bank accounts. Victim Ramesh Kumar (9431100001) complained of a loss
of Rs.64,000 on 06/03/2024 after the caller warned that the account blocked.
"""
    txns = table_to_csv(
        [
            "timestamp", "txn_id", "from_account", "from_upi", "from_name", "from_bank",
            "to_account", "to_upi", "to_name", "to_bank", "amount_inr", "channel", "remarks",
        ],
        [
            ["2024-03-06T10:05:00", "T1001", "5001000123456", "ramesh.kumar@ybl", "Ramesh Kumar",
             "HDFC", "5001000987654", "mule1@ybl", "Deepak Roy", "PUNB", "64000", "UPI", "fraud debit"],
            ["2024-03-06T10:20:00", "T1002", "5001000987654", "mule1@ybl", "Deepak Roy",
             "PUNB", "5001000000001", "anup.saha@okaxis", "Anup Saha", "UCO", "60000", "UPI", "cashout"],
        ],
    )
    calls = table_to_csv(
        ["call_id", "timestamp", "msisdn_a", "msisdn_b", "duration_sec", "cell_id", "imei_a", "imei_b"],
        [["C0001", "2024-03-06T09:50:00", "9431100002", "9431100001", "48", "CEL101", "", ""]],
    )
    sim = table_to_csv(
        ["msisdn", "iccid", "imei", "activation_date", "status", "provider", "owner_name", "remarks"],
        [
            ["9431100001", "89012345678901234567", "356938035643801", "2024-03-05", "active",
             "Airtel", "Ramesh Kumar", "victim SIM reissued after spoofed KYC update"],
            ["9431100001", "89914700000000000001", "356938035643802", "2024-03-06", "active",
             "Airtel", "Anup Saha", "operator SIM used for OTP relay"],
        ],
    )
    readme = """CFNA INPUT TEMPLATE
===================

Hand these files to CFNA, either one at a time or together:

  python -m cfna new --title "My case" --file incident_notes.txt --file transactions.csv
  python -m cfna new                      (interactive wizard)
  python -m cfna run <case_dir>           (if you already built the folder yourself)

What matters is the CONTENT, not the file name:

  * narrative .txt/.md/.log  -> free text; identifiers (account, UPI, phone, IMEI,
    ICCID, IFSC, PAN, IP) and role words (kingpin, recruiter, operator, mule,
    victim) are extracted automatically.
  * .csv                     -> kind is sniffed from the header, so
      transactions need amount/txn/debit/credit columns,
      call logs need msisdn/duration/caller/callee,
      SIM registry needs iccid/imei/msisdn,
      device logs need imei/app_version/session/ip_address.
  * .json / .jsonl           -> list of objects, or {"records": [...]}.
  * case.json                -> optional metadata (title, police station, dates).

Every row and every sentence is traceable: the report cites the source file and line.
"""
    return [
        ("case.json", json.dumps({
            "case_id": "sample_case",
            "title": "Sample SIM-swap case",
            "police_station": "Cyber Crime Police Station",
            "district": "Sample District",
            "state": "Sample State",
            "complainant": "Ramesh Kumar",
            "occurred_on": "2024-03-06",
            "reported_on": "2024-03-06",
            "officer": "IO, Cyber Crime",
        }, indent=2)),
        ("incident_notes.txt", notes),
        ("transactions.csv", txns),
        ("call_logs.csv", calls),
        ("sim_device_registry.csv", sim),
        ("README.txt", readme),
    ]


def write_template(dest: Path) -> Path:
    target = dest / "cfna_input_template"
    target.mkdir(parents=True, exist_ok=True)
    for name, body in template_files():
        (target / name).write_text(body, encoding="utf-8")
    return target

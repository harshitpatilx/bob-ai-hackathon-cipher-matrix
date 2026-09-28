from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable

from cfna.models import CaseMeta, Document

TEXT_SUFFIXES = {".txt", ".md", ".log", ".statement"}
JSON_SUFFIXES = {".json", ".jsonl"}

CSV_KINDS = {
    "transactions": "transactions",
    "txn": "transactions",
    "upi": "transactions",
    "call": "call_logs",
    "cdr": "call_logs",
    "sim": "sim_registry",
    "device": "device_logs",
    "imei": "device_logs",
}

HEADER_HINTS = {
    "transactions": ["amount_inr", "amount", "debit", "credit", "txn_id"],
    "call_logs": ["msisdn", "duration", "caller", "callee"],
    "sim_registry": ["iccid", "sim_no", "imei", "msisdn"],
    "device_logs": ["imei", "app_version", "session", "ip_address"],
}


def _kind_from_name(name: str) -> str:
    lowered = name.lower()
    for key, kind in CSV_KINDS.items():
        if key in lowered:
            return kind
    return "records"


def _kind_from_header(header: list[str]) -> str | None:
    cols = [h.strip().lower() for h in header]
    best_kind: str | None = None
    best_hits = 0
    for kind, hints in HEADER_HINTS.items():
        hits = sum(1 for hint in hints if any(hint in c for c in cols))
        if hits > best_hits:
            best_hits = hits
            best_kind = kind
    return best_kind if best_hits >= 2 else None


def load_text_file(path: Path) -> Document:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return Document(path=path.name, kind="narrative", text=text, lines=lines)


def load_json_file(path: Path) -> list[dict[str, Any]]:
    raw = path.read_text(encoding="utf-8", errors="replace").strip()
    if not raw:
        return []
    if path.suffix.lower() == ".jsonl":
        rows = []
        for line in raw.splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
        return rows
    data = json.loads(raw)
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        for key in ("records", "rows", "data", "items"):
            if isinstance(data.get(key), list):
                return [row for row in data[key] if isinstance(row, dict)]
        return [data]
    return []


def load_csv_file(path: Path) -> tuple[str, list[dict[str, Any]]]:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as fh:
        reader = csv.DictReader(fh)
        header = list(reader.fieldnames or [])
        rows = [{k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()} for row in reader]
    kind = _kind_from_header(header) or _kind_from_name(path.name)
    return kind, rows


def load_case_dir(case_dir: Path) -> tuple[CaseMeta, list[Document], list[dict[str, Any]]]:
    meta = CaseMeta()
    documents: list[Document] = []
    records: list[dict[str, Any]] = []

    if not case_dir.is_dir():
        raise FileNotFoundError(f"case directory not found: {case_dir}")

    for path in sorted(case_dir.iterdir()):
        if path.is_dir():
            continue
        suffix = path.suffix.lower()
        lowered = path.name.lower()
        if lowered in {"truth.json", "ground_truth.json"}:
            continue
        if lowered in {"case.json", "meta.json", "case_meta.json"}:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            for field in (
                "case_id", "title", "police_station", "district", "state",
                "complainant", "occurred_on", "reported_on", "officer", "notes",
            ):
                if field in data:
                    setattr(meta, field, str(data[field]))
            continue
        if suffix == ".csv":
            kind, rows = load_csv_file(path)
            for row in rows:
                row["__kind"] = kind
                row["__source"] = path.name
                records.append(row)
            documents.append(Document(path=path.name, kind="structured", text="", lines=[]))
        elif suffix in JSON_SUFFIXES:
            rows = load_json_file(path)
            for row in rows:
                kind = str(row.pop("__kind", _kind_from_name(path.name)))
                row["__kind"] = kind
                row["__source"] = path.name
                records.append(row)
            documents.append(Document(path=path.name, kind="structured", text="", lines=[]))
        elif suffix in TEXT_SUFFIXES:
            doc = load_text_file(path)
            if "statement" in lowered:
                doc.kind = "statement"
            elif "complaint" in lowered or "victim" in lowered:
                doc.kind = "complaint"
            elif "note" in lowered or "intel" in lowered or "brief" in lowered:
                doc.kind = "intel_note"
            documents.append(doc)

    if meta.case_id == "case":
        meta.case_id = case_dir.name
    if not meta.title or meta.title == "Cyber Fraud Case":
        meta.title = case_dir.name.replace("_", " ").replace("-", " ").title()
    return meta, documents, records


def discover_case_dirs(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    direct = [p for p in sorted(root.iterdir()) if p.is_dir() and any(p.iterdir())]
    if direct:
        return direct
    return [root]


def iter_record_rows(records: Iterable[dict[str, Any]], kind: str) -> Iterable[dict[str, Any]]:
    for row in records:
        if row.get("__kind") == kind:
            yield row

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cfna.analysis import (
    assign_roles,
    build_evidence,
    build_hierarchy,
    build_timeline,
    classify_patterns,
    compute_metrics,
    score_risk,
    summarize_roles,
)
from cfna.bob import BobAgent
from cfna.extract import extract_all, extract_text_relations
from cfna.ingest import load_case_dir
from cfna.models import CaseBrief, CaseGraph, now_iso
from cfna.report import render_fir, render_html


def build_case(case_dir: Path) -> tuple[CaseGraph, Any]:
    meta, documents, records = load_case_dir(case_dir)
    case = CaseGraph(meta=meta)
    case.documents.extend(documents)
    case.records.extend(records)
    extract_all(case, documents, records)
    extract_text_relations(case, documents)
    return case, (documents, records)


def analyze(case: CaseGraph, bob: BobAgent | None = None) -> tuple[CaseBrief, Any, dict[str, list[dict]]]:
    bob = bob or BobAgent()
    metrics = compute_metrics(case)
    patterns = classify_patterns(case, metrics)
    assessments = assign_roles(case, metrics)
    score_risk(case, metrics, assessments)
    hierarchy = build_hierarchy(case, assessments)
    timeline = build_timeline(case)
    evidence = build_evidence(case, metrics, assessments)
    agent_output = bob.reason(case, metrics, patterns, assessments, timeline)

    legal: list[str] = []
    actions: list[str] = []
    if patterns:
        legal = list(patterns[0].legal)
        for extra in patterns[1:]:
            for item in extra.legal:
                if item not in legal:
                    legal.append(item)

    brief = CaseBrief(
        meta=case.meta,
        generated_at=now_iso(),
        patterns=patterns,
        assessments=assessments,
        hierarchy=hierarchy,
        timeline=timeline,
        stats={**case.stats(), "role_counts": summarize_roles(assessments), "flow_total": round(metrics.total_flow, 2)},
        insights=agent_output["insights"],
        gaps=agent_output["gaps"],
        evidence=evidence,
        actions=agent_output["actions"],
        legal=legal or ["IT Act 2000 s.66C / s.66D", "BNS 2023 s.318 cheating [IPC 420]", "BNS 2023 s.61 conspiracy [IPC 120B]"],
    )
    return brief, metrics, evidence


def export_outputs(
    case: CaseGraph,
    brief: CaseBrief,
    metrics: Any,
    evidence: dict[str, list[dict]],
    out_dir: Path,
) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}

    html_path = out_dir / "report.html"
    html_path.write_text(render_html(case, brief, metrics, evidence), encoding="utf-8")
    written["report.html"] = html_path

    fir_path = out_dir / "fir_brief.md"
    fir_path.write_text(render_fir(case, brief, metrics, evidence), encoding="utf-8")
    written["fir_brief.md"] = fir_path

    data_path = out_dir / "case_data.json"
    data_path.write_text(
        json.dumps({"case": case.to_dict(), "brief": brief.to_dict()}, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    written["case_data.json"] = data_path

    network_path = out_dir / "network.json"
    network_path.write_text(
        json.dumps(
            {
                "nodes": [
                    {"id": node, "role": brief.assessments[node].role, "risk": brief.assessments[node].risk}
                    for node in brief.assessments
                ],
                "edges": [rel.to_dict() for rel in case.relation_list()],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    written["network.json"] = network_path
    return written


def run_case(case_dir: Path, out_root: Path | None = None) -> dict[str, Any]:
    case, _ = build_case(case_dir)
    brief, metrics, evidence = analyze(case)
    out_dir = (out_root or case_dir.parent.parent / "output") / case.meta.case_id
    written = export_outputs(case, brief, metrics, evidence, out_dir)
    return {
        "case": case,
        "brief": brief,
        "metrics": metrics,
        "evidence": evidence,
        "outputs": {name: str(path) for name, path in written.items()},
        "out_dir": str(out_dir),
    }

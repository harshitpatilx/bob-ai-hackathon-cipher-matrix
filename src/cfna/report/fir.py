from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from cfna.analysis.hierarchy import summarize_roles
from cfna.analysis.metrics import GraphMetrics
from cfna.analysis.timeline import burst_windows, first_last
from cfna.models import ROLE_KINGPIN, ROLE_MULE, ROLE_OPERATOR, ROLE_RECRUITER, ROLE_VICTIM, CaseBrief, CaseGraph


def _fmt_amount(value: float) -> str:
    return f"{value:,.2f}"


def _facts_paragraph(case: CaseGraph, brief: CaseBrief, metrics: GraphMetrics) -> list[str]:
    pattern = brief.primary
    first, last = first_last(brief.timeline)
    transfers = [rel for rel in case.relation_list() if rel.rtype == "transfer"]
    total = metrics.total_flow
    parties = len([m for m in metrics.nodes.values() if m.in_amount or m.out_amount])
    paragraphs: list[str] = []
    window = f"between {first} and {last}" if first and last else "during the period referred to in the complaint"
    paragraphs.append(
        f"That the complainant herein was defrauded of money through the misuse of digital payment systems. "
        f"It is alleged that {window}, fraudulent transactions aggregating to Rs.{_fmt_amount(total)} were "
        f"executed involving {parties} financial/telecom identifiers, which stand captured in the "
        f"transaction annexure of this case file."
    )
    if pattern:
        paragraphs.append(
            f"The technical analysis of the material on record points to the modus operandi of "
            f"{pattern.name} ({pattern.id}). {pattern.summary}"
        )
    roles = summarize_roles(brief.assessments)
    kingpins = [a for a in brief.assessments.values() if a.role == ROLE_KINGPIN]
    mules = [a for a in brief.assessments.values() if a.role == ROLE_MULE]
    victims = [a for a in brief.assessments.values() if a.role == ROLE_VICTIM]
    if kingpins:
        names = ", ".join(k.node_id.split(":", 1)[1] for k in kingpins[:3])
        paragraphs.append(
            f"The money trail converges on {len(kingpins)} terminal beneficiary account(s)/identifier(s) "
            f"({names}) which show no commensurate legitimate credit, indicating that these accounts are the "
            f"end of the layering chain controlled by the kingpin of the syndicate."
        )
    if mules:
        paragraphs.append(
            f"A total of {len(mules)} mule account(s) have been identified which received the defrauded money "
            f"and forwarded 85% or more of their inflow to the next layer, demonstrating the organised "
            f"pass-through structure of the network."
        )
    if victims:
        victim_loss = sum(
            m.loss_amount for node, m in metrics.nodes.items()
            if node in brief.assessments and brief.assessments[node].role == ROLE_VICTIM
        )
        paragraphs.append(
            f"{len(victims)} victim identifier(s) are recorded in the annexure with quantified loss of "
            f"Rs.{_fmt_amount(victim_loss)}; their statements be recorded under s.180 BNSS (03) 2023."
        )
    bursts = burst_windows(brief.timeline)
    if bursts:
        biggest = max(bursts, key=lambda b: b["amount"])
        paragraphs.append(
            f"{len(bursts)} rapid transfer burst(s) were detected, the largest being {biggest['count']} "
            f"transfers worth Rs.{_fmt_amount(biggest['amount'])} inside a {biggest['window_minutes']}-minute "
            f"window, indicative of automated/organised layering rather than genuine commerce."
        )
    return paragraphs


def _tree_lines(case: CaseGraph, brief: CaseBrief) -> list[str]:
    order = [ROLE_KINGPIN, ROLE_OPERATOR, ROLE_RECRUITER, ROLE_MULE, ROLE_VICTIM]
    lines: list[str] = []
    mules = brief.hierarchy.get(ROLE_MULE, [])
    kingpins = brief.hierarchy.get(ROLE_KINGPIN, [])
    sink_set = set(kingpins)
    tier_groups: dict[int, list[str]] = {}
    for node in mules:
        tier = brief.assessments[node].tier if node in brief.assessments else 0
        tier_groups.setdefault(tier, []).append(node)

    if kingpins:
        lines.append(f"KINGPIN (terminal beneficiary)")
        for node in kingpins[:3]:
            lines.append(f"  |-- {_short(node)}")
    for tier in sorted(tier_groups):
        label = f"Tier-{tier}" if tier else "Mule (layer not established)"
        lines.append(f"  |-- {label}")
        for node in tier_groups[tier][:6]:
            lines.append(f"  |     |-- {_short(node)}")
        if len(tier_groups[tier]) > 6:
            lines.append(f"  |     |-- ... {len(tier_groups[tier]) - 6} more")
    for role in (ROLE_OPERATOR, ROLE_RECRUITER, ROLE_VICTIM):
        members = brief.hierarchy.get(role, [])
        if not members:
            continue
        lines.append(f"  |-- {role.upper()} ({len(members)})")
        for node in members[:6]:
            lines.append(f"  |     |-- {_short(node)}")
        if len(members) > 6:
            lines.append(f"  |     |-- ... {len(members) - 6} more")
    return lines


def _short(node_id: str) -> str:
    return node_id.split(":", 1)[1]


def _table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    if not rows:
        return ["_none recorded in the dataset_"]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        cells = [str(cell).replace("|", "/").replace("\n", " ") for cell in row]
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def render_fir(case: CaseGraph, brief: CaseBrief, metrics: GraphMetrics, evidence: dict[str, list[dict]]) -> str:
    meta = case.meta
    pattern = brief.primary
    now = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")
    lines: list[str] = []

    lines += [
        f"# DRAFT FIR / CASE BRIEF - {meta.title}",
        "",
        f"**Case file:** {meta.case_id}  ",
        f"**Police Station:** {meta.police_station or '________________'}  ",
        f"**District:** {meta.district or '________________'}  ",
        f"**State:** {meta.state or '________________'}  ",
        f"**Complainant:** {meta.complainant or '________________'}  ",
        f"**Date of occurrence:** {meta.occurred_on or '________________'}  ",
        f"**Date of reporting:** {meta.reported_on or '________________'}  ",
        f"**Generated:** {now} by CFNA (Bob backend: rule-assisted network analysis)",
        "",
        "> Draft prepared for review by the Investigating Officer. Sections, jurisdiction and",
        "> witness details must be verified against the case diary before filing u/s 173 BNSS, 2023.",
        "",
        "---",
        "",
        "## 1. Case at a glance",
        "",
    ]

    primary_label = f"{pattern.name} (confidence {int(pattern.score * 100)}%)" if pattern else "not established"
    roles = summarize_roles(brief.assessments)
    lines += _table(
        ["Parameter", "Value"],
        [
            ["Fraud pattern identified", primary_label],
            ["Entities extracted", brief.stats.get("entities", 0)],
            ["Relationships extracted", brief.stats.get("relations", 0)],
            ["Documents processed", brief.stats.get("documents", 0)],
            ["Structured records", brief.stats.get("records", 0)],
            ["Money trail volume", f"Rs.{_fmt_amount(metrics.total_flow)}"],
            ["Kingpins / Operators / Recruiters", f"{roles.get('kingpin', 0)} / {roles.get('operator', 0)} / {roles.get('recruiter', 0)}"],
            ["Mule accounts", roles.get("mule", 0)],
            ["Victim identifiers", roles.get("victim", 0)],
            ["Connected components", len(metrics.components)],
            ["Highest risk node", next((f"{_short(a.node_id)} ({a.risk}/99)" for a in sorted(brief.assessments.values(), key=lambda x: -x.risk) if a.role != "victim"), "-")],
        ],
    )
    lines.append("")

    lines += ["## 2. Facts of the case", ""]
    for paragraph in _facts_paragraph(case, brief, metrics):
        lines += [paragraph, ""]

    lines += ["## 3. Modus operandi / fraud pattern analysis", ""]
    if pattern:
        lines += [f"**{pattern.name} ({pattern.id})** - {pattern.summary}", "", "Signals relied upon:"]
        lines += [f"{idx}. {signal}" for idx, signal in enumerate(pattern.signals, 1)] or ["_n/a_"]
        lines.append("")
        if len(brief.patterns) > 1:
            runner = brief.patterns[1]
            lines.append(
                f"Secondary pattern on record: {runner.name} at {int(runner.score * 100)}% confidence "
                f"({runner.summary})"
            )
            lines.append("")

    lines += ["## 4. Organisational hierarchy (kingpin -> operator -> mule -> victim)", "", "```"]
    tree = _tree_lines(case, brief)
    lines += tree if tree else ["hierarchy could not be established"]
    lines += ["```", ""]

    lines += ["### 4.1 Accused / suspect assessment", ""]
    accused_rows = []
    for assessment in sorted(brief.assessments.values(), key=lambda a: (-a.risk, a.role)):
        if assessment.role in {"victim", "unknown"}:
            continue
        ent = case.entities.get(assessment.node_id)
        reasons = "; ".join(assessment.reasons[:2])
        accused_rows.append(
            [
                _short(assessment.node_id),
                ent.etype.value if ent else "-",
                assessment.role,
                f"T{assessment.tier}" if assessment.tier else "-",
                assessment.risk,
                reasons[:150],
            ]
        )
    lines += _table(["Identifier", "Type", "Role", "Tier", "Risk", "Basis of assessment"], accused_rows[:30])
    lines.append("")

    lines += ["## 5. Financial trail - accounts to be frozen", ""]
    freeze_rows = []
    for row in evidence.get("accounts_freeze_list", []):
        if not row["freeze"]:
            continue
        freeze_rows.append(
            [
                row["identifier"],
                row["type"],
                row["bank"] or "-",
                row["upi"] or "-",
                _fmt_amount(row["in_amount"]),
                _fmt_amount(row["out_amount"]),
                row["role"],
                f"T{row['tier']}" if row["tier"] else "-",
            ]
        )
    lines += _table(
        ["Identifier", "Type", "Bank", "UPI handle", "Inflow (Rs.)", "Outflow (Rs.)", "Role", "Tier"],
        freeze_rows[:40],
    )
    lines.append("")

    lines += ["### 5.1 Largest recorded transfers", ""]
    transfer_rows = [
        [t["when"], t["from"], t["to"], _fmt_amount(t["amount"]), t["evidence"][:80]]
        for t in evidence.get("largest_transfers", [])
    ]
    lines += _table(["When", "From", "To", "Amount (Rs.)", "Source remark"], transfer_rows)
    lines.append("")

    lines += ["## 6. Victim annexure", ""]
    victim_rows = [
        [v["identifier"], v["type"], _fmt_amount(v["amount_lost"]), ", ".join(v["paid_to"])]
        for v in evidence.get("victims", [])
    ]
    lines += _table(["Victim identifier", "Type", "Amount lost (Rs.)", "Paid into"], victim_rows[:40])
    lines.append("")

    lines += ["## 7. Telecom / device evidence", ""]
    lines.append("### 7.1 SIM-swap bindings (MSISDN with more than one SIM / re-issued SIM)")
    lines.append("")
    sim_rows = []
    for row in evidence.get("sim_swap_bindings", []):
        bindings = "; ".join(
            f"{b['iccid']} since {b['since'] or b['activation'] or 'n/a'} ({b['status'] or 'status n/a'})"
            for b in row["bindings"]
        )
        sim_rows.append([row["msisdn"], row.get("owner") or "-", row["sim_count"], bindings])
    lines += _table(["MSISDN", "Subscriber", "#SIMs", "SIM bindings (ICCID, activation, status)"], sim_rows)
    lines.append("")
    lines.append("### 7.2 Devices (IMEI) and identities used")
    lines.append("")
    device_rows = [
        [d["imei"], d["sim_count"], d["msisdn_count"], ", ".join(d["sims"][:3]), ", ".join(d["msisdns"][:3])]
        for d in evidence.get("devices", [])
    ]
    lines += _table(["IMEI", "#SIMs", "#MSISDNs", "SIMs", "MSISDNs"], device_rows[:30])
    lines.append("")
    lines.append("### 7.3 Call detail record highlights")
    lines.append("")
    call_rows = [
        [c["from"], c["to"], c["count"], c["first"] or "-", c["evidence"][:70]]
        for c in evidence.get("call_records", [])
    ]
    lines += _table(["Calling MSISDN", "Called MSISDN", "CDR count", "First seen", "Note"], call_rows[:30])
    lines.append("")

    lines += ["## 8. Timeline of occurrences", ""]
    timeline_rows = [
        [e.ts, e.etype, e.summary[:110]]
        for e in brief.timeline
        if e.etype in {"transfer", "sim_activation", "sim_event", "offence", "report"}
    ][:40]
    lines += _table(["Timestamp", "Event", "Detail"], timeline_rows)
    first, last = first_last(brief.timeline)
    if first:
        lines += ["", f"**Period:** {first} to {last}", ""]
    bursts = burst_windows(brief.timeline)
    if bursts:
        lines += ["**Rapid transfer bursts:**", ""]
        lines += _table(
            ["Start", "End", "Transfers", "Amount (Rs.)"],
            [[b["start"], b["end"], b["count"], _fmt_amount(b["amount"])] for b in bursts[:10]],
        )
        lines.append("")

    lines += ["## 9. Sections of law invoked", ""]
    legal = brief.legal or []
    lines += [f"{idx}. {item}" for idx, item in enumerate(legal, 1)]
    lines += [
        "",
        "_Note: BNS 2023 applies to offences from 01 July 2024; for offences before that date, the ",
        "corresponding IPC sections recorded in brackets are to be invoked. PMLA applicability to be ",
        "confirmed by the IO with the ED regional office._",
        "",
    ]

    lines += ["## 10. Recommended investigation actions", ""]
    lines += [f"{idx}. {action}" for idx, action in enumerate(brief.actions, 1)]
    lines.append("")

    lines += ["## 11. Intelligence gaps flagged by Bob", ""]
    if brief.gaps:
        lines += [f"- {gap}" for gap in brief.gaps]
    else:
        lines += ["- None flagged; the dataset is internally consistent."]
    lines.append("")

    lines += ["## 12. Analyst (Bob) key observations", ""]
    lines += [f"- {insight}" for insight in brief.insights]
    lines.append("")

    lines += [
        "## Annexures",
        "",
        "A. Transaction ledger (certified statements to be obtained under s.91 BNSS)",
        "B. Call detail records of accused MSISDNs",
        "C. SIM / device mapping (ICCID - MSISDN - IMEI)",
        "D. Bank accounts freeze chart with IFSC and KYC status",
        "E. Victim loss chart",
        "F. Network graph (see `report.html` for the interactive graph)",
        "G. Underlying machine-readable analysis (`case_data.json`)",
        "",
        "---",
        "",
        f"**Place:** {meta.district or '________________'}  ",
        f"**Date:** {datetime.now(timezone.utc).strftime('%d %m %Y')}  ",
        "",
        "_______________________________  ",
        f"{meta.officer or 'Investigating Officer'}  ",
        f"{meta.police_station or 'Police Station'}",
        "",
    ]
    return "\n".join(lines)

from __future__ import annotations

from typing import Any

from cfna.analysis.metrics import GraphMetrics
from cfna.models import CaseGraph, EntityType, NodeAssessment

ACCOUNT_TYPES = {EntityType.ACCOUNT, EntityType.UPI_ID, EntityType.CARD}


def _short(node_id: str) -> str:
    return node_id.split(":", 1)[1]


def bank_table(case: CaseGraph, metrics: GraphMetrics, assessments: dict[str, NodeAssessment]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    upi_by_account: dict[str, list[str]] = {}
    for rel in case.relation_list():
        if rel.rtype == "maps_to":
            upi_by_account.setdefault(rel.dst, []).append(_short(rel.src))
    for node, metric in metrics.nodes.items():
        ent = case.entities.get(node)
        if ent is None or ent.etype not in ACCOUNT_TYPES:
            continue
        if metric.in_amount <= 0 and metric.out_amount <= 0:
            continue
        assessment = assessments.get(node)
        rows.append(
            {
                "identifier": _short(node),
                "type": ent.etype.value,
                "bank": ent.attrs.get("bank", ""),
                "upi": ", ".join(sorted(set(upi_by_account.get(node, []))))[:60],
                "in_amount": round(metric.in_amount, 2),
                "out_amount": round(metric.out_amount, 2),
                "net": round(metric.net_amount, 2),
                "parties_in": metric.in_deg,
                "parties_out": metric.out_deg,
                "role": assessment.role if assessment else "unknown",
                "tier": assessment.tier if assessment else 0,
                "risk": assessment.risk if assessment else 0.0,
                "freeze": bool(assessment and assessment.role in {"kingpin", "operator", "recruiter", "mule"}),
            }
        )
    rows.sort(key=lambda r: (r["role"] != "kingpin", -(r["in_amount"] + r["out_amount"])))
    return rows


def device_table(case: CaseGraph, metrics: GraphMetrics) -> list[dict[str, Any]]:
    sims_by_device: dict[str, set[str]] = {}
    phones_by_device: dict[str, set[str]] = {}
    ips_by_device: dict[str, set[str]] = {}
    for rel in case.relation_list():
        if rel.rtype in {"device_used_sim"}:
            sims_by_device.setdefault(rel.src, set()).add(_short(rel.dst))
        elif rel.rtype == "device_used_msisdn":
            phones_by_device.setdefault(rel.src, set()).add(_short(rel.dst))
        elif rel.rtype == "session_ip":
            ips_by_device.setdefault(rel.src, set()).add(_short(rel.dst))
    rows: list[dict[str, Any]] = []
    for entity in case.entities.values():
        if entity.etype != EntityType.DEVICE:
            continue
        sims = sims_by_device.get(entity.id, set())
        phones = phones_by_device.get(entity.id, set())
        ips = ips_by_device.get(entity.id, set())
        if not sims and not phones:
            continue
        rows.append(
            {
                "imei": entity.norm,
                "sims": sorted(sims),
                "sim_count": len(sims),
                "msisdns": sorted(phones),
                "msisdn_count": len(phones),
                "ips": sorted(ips),
                "swap_signature": len(sims) >= 2 or len(phones) >= 2,
            }
        )
    rows.sort(key=lambda r: (-(r["sim_count"] + r["msisdn_count"]), r["imei"]))
    return rows


def sim_swap_table(case: CaseGraph) -> list[dict[str, Any]]:
    sims_by_phone: dict[str, list[tuple[str, str]]] = {}
    for rel in case.relation_list():
        if rel.rtype == "sim_bound_to_msisdn":
            sims_by_phone.setdefault(rel.dst, []).append((rel.src, rel.first_ts))
    multi = {phone: links for phone, links in sims_by_phone.items() if len(links) >= 2}
    rows: list[dict[str, Any]] = []
    for phone, links in sorted(multi.items()):
        bindings = []
        for sim, ts in sorted(links):
            entity = case.entities.get(sim)
            bindings.append(
                {
                    "iccid": _short(sim),
                    "since": ts,
                    "activation": entity.attrs.get("activation_date", "") if entity else "",
                    "status": entity.attrs.get("status", "") if entity else "",
                }
            )
        phone_ent = case.entities.get(phone)
        rows.append(
            {
                "msisdn": _short(phone),
                "owner": str(phone_ent.attrs.get("owner_name", "")) if phone_ent else "",
                "sim_count": len(links),
                "bindings": bindings,
            }
        )
    return rows


def top_transfers(case: CaseGraph, limit: int = 25) -> list[dict[str, Any]]:
    transfers = [rel for rel in case.relation_list() if rel.rtype == "transfer"]
    transfers.sort(key=lambda r: r.amount, reverse=True)
    rows = []
    for rel in transfers[:limit]:
        rows.append(
            {
                "from": _short(rel.src),
                "to": _short(rel.dst),
                "amount": round(rel.amount, 2),
                "when": rel.first_ts,
                "evidence": rel.evidence[0] if rel.evidence else "",
            }
        )
    return rows


def call_table(case: CaseGraph, limit: int = 25) -> list[dict[str, Any]]:
    calls = [rel for rel in case.relation_list() if rel.rtype == "call"]
    calls.sort(key=lambda r: r.count, reverse=True)
    return [
        {
            "from": _short(rel.src),
            "to": _short(rel.dst),
            "count": rel.count,
            "first": rel.first_ts,
            "evidence": rel.evidence[0] if rel.evidence else "",
        }
        for rel in calls[:limit]
    ]


def victim_table(case: CaseGraph, metrics: GraphMetrics, assessments: dict[str, NodeAssessment]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for node, assessment in assessments.items():
        if assessment.role != "victim":
            continue
        metric = metrics.nodes.get(node)
        ent = case.entities.get(node)
        if metric is None or ent is None:
            continue
        rows.append(
            {
                "identifier": _short(node),
                "type": ent.etype.value,
                "amount_lost": round(metric.loss_amount, 2),
                "paid_to": sorted(
                    rel.dst.split(":", 1)[1]
                    for rel in case.relation_list()
                    if rel.rtype == "transfer" and rel.src == node
                )[:4],
            }
        )
    rows.sort(key=lambda r: -r["amount_lost"])
    return rows


def build_evidence(case: CaseGraph, metrics: GraphMetrics, assessments: dict[str, NodeAssessment]) -> dict[str, list[dict[str, Any]]]:
    return {
        "accounts_freeze_list": bank_table(case, metrics, assessments),
        "devices": device_table(case, metrics),
        "sim_swap_bindings": sim_swap_table(case),
        "largest_transfers": top_transfers(case),
        "call_records": call_table(case),
        "victims": victim_table(case, metrics, assessments),
    }

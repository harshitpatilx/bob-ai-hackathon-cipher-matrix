from __future__ import annotations

from typing import Iterable

from cfna.analysis.metrics import GraphMetrics, NodeMetrics
from cfna.graph import DiGraph, hop_distance
from cfna.models import (
    ROLE_KINGPIN,
    ROLE_MULE,
    ROLE_OPERATOR,
    ROLE_RECRUITER,
    ROLE_UNKNOWN,
    ROLE_VICTIM,
    CaseGraph,
    Entity,
    EntityType,
    NodeAssessment,
)

MULE_MIN_IN = 5000.0
PASS_THROUGH = 0.85
# A narrative can name the same sentence's actors with two roles; the higher rung always wins so
# "Kingpin Anup Saha ... victim Ramesh Kumar" does not turn the kingpin into a victim.
STRONG_ROLES = ("kingpin", "operator", "recruiter", "mule")


def _entity(case: CaseGraph, node_id: str) -> Entity | None:
    return case.entities.get(node_id)


def _has_label(metrics: GraphMetrics, node_id: str, label: str) -> bool:
    metric = metrics.nodes.get(node_id)
    return bool(metric and label in metric.labels)


def _is_identifier(case: CaseGraph, node_id: str) -> bool:
    ent = _entity(case, node_id)
    return bool(ent and ent.etype in {EntityType.ACCOUNT, EntityType.UPI_ID, EntityType.PHONE, EntityType.CARD})


def _money_nodes(case: CaseGraph, metrics: GraphMetrics) -> list[str]:
    return [
        node for node, metric in metrics.nodes.items()
        if (metric.in_amount > 0 or metric.out_amount > 0) and _is_identifier(case, node)
    ]


def _pass_through(metric: NodeMetrics) -> bool:
    return metric.in_amount >= MULE_MIN_IN and metric.pass_through >= PASS_THROUGH


def _has_strong_label(metrics: GraphMetrics, node_id: str) -> bool:
    metric = metrics.nodes.get(node_id)
    return bool(metric and any(label in metric.labels for label in STRONG_ROLES))


def _victims(case: CaseGraph, metrics: GraphMetrics) -> set[str]:
    victims: set[str] = set()
    for node in _money_nodes(case, metrics):
        metric = metrics.nodes[node]
        if metric.in_amount > 0:
            continue
        if metric.out_amount <= 0 or metric.flow_out_deg == 0:
            continue
        if metric.flow_in_deg >= 2:
            continue
        if _has_strong_label(metrics, node):
            continue
        victims.add(node)
        ent = _entity(case, node)
        if ent is not None:
            ent.add_label("victim")
    for node, metric in metrics.nodes.items():
        if "victim" in metric.labels and metric.in_amount == 0 and not _has_strong_label(metrics, node):
            victims.add(node)
    return victims


def _mules(case: CaseGraph, metrics: GraphMetrics, victims: set[str]) -> set[str]:
    mules: set[str] = set()
    for node in _money_nodes(case, metrics):
        if node in victims:
            continue
        metric = metrics.nodes[node]
        if _pass_through(metric) or "mule" in metric.labels:
            if any(label in metric.labels for label in ("kingpin", "operator", "recruiter")):
                continue
            mules.add(node)
    for node, metric in metrics.nodes.items():
        if node in victims or "mule" not in metric.labels:
            continue
        if any(label in metric.labels for label in ("kingpin", "operator", "recruiter")):
            continue
        mules.add(node)
    return mules


def _operators(case: CaseGraph, metrics: GraphMetrics, excluded: set[str]) -> set[str]:
    operators: set[str] = set()
    device_sims: dict[str, set[str]] = {}
    phone_devices: dict[str, set[str]] = {}
    for rel in case.relations.values():
        if rel.rtype == "device_used_sim":
            device_sims.setdefault(rel.src, set()).add(rel.dst)
        elif rel.rtype in {"device_used_msisdn", "device_used_sim"}:
            phone_devices.setdefault(rel.dst, set()).add(rel.src)
        elif rel.rtype == "sim_bound_to_msisdn":
            phone_devices.setdefault(rel.dst, set()).add(rel.src)
    for device, sims in device_sims.items():
        if len(sims) >= 3:
            operators.add(device)
    for phone, devices in phone_devices.items():
        if len(devices) >= 2 and phone not in excluded:
            operators.add(phone)
    for node, metric in metrics.nodes.items():
        if "operator" in metric.labels:
            operators.add(node)
        elif "kingpin" in metric.labels and node.startswith("person:"):
            operators.add(node)
    return {node for node in operators if node not in excluded}


def _recruiters(case: CaseGraph, metrics: GraphMetrics, mules: set[str], excluded: set[str]) -> set[str]:
    recruiters: set[str] = set()
    for node, metric in metrics.nodes.items():
        if node in excluded:
            continue
        if "recruiter" in metric.labels:
            if any(label in metric.labels for label in ("kingpin", "operator", "mule")):
                continue
            recruiters.add(node)
            continue
        if metric.in_amount > 0 or node in mules:
            continue
        linked_mules = 0
        for rel in case.relations.values():
            if rel.rtype not in {"call", "owns"}:
                continue
            if rel.src != node and rel.dst != node:
                continue
            other = rel.dst if rel.src == node else rel.src
            if other in mules and other != node:
                linked_mules += 1
        if linked_mules >= 3:
            recruiters.add(node)
    return recruiters


def _kingpins(
    case: CaseGraph,
    metrics: GraphMetrics,
    excluded: set[str],
    max_count: int = 2,
) -> set[str]:
    labelled = {
        node for node, metric in metrics.nodes.items()
        if "kingpin" in metric.labels and node not in excluded
    }
    candidates = [
        node for node in _money_nodes(case, metrics)
        if node not in excluded and metrics.nodes[node].in_amount > 0
    ]
    if not candidates and labelled:
        return labelled
    max_in = max((metrics.nodes[n].in_amount for n in candidates), default=0.0)
    max_pr = max((metrics.nodes[n].pagerank for n in candidates), default=0.0)
    max_bc = max((metrics.nodes[n].betweenness for n in candidates), default=0.0)

    scored: list[tuple[float, str]] = []
    for node in candidates:
        metric = metrics.nodes[node]
        if metric.pass_through >= PASS_THROUGH:
            continue
        if max_in > 0 and metric.in_amount < 0.25 * max_in:
            continue
        score = 0.0
        if max_in:
            score += 0.5 * (metric.in_amount / max_in)
        if max_pr:
            score += 0.25 * (metric.pagerank / max_pr)
        if max_bc:
            score += 0.25 * (metric.betweenness / max_bc)
        if metric.in_deg >= 3:
            score += 0.1
        scored.append((score, node))
    scored.sort(reverse=True)
    result = set(labelled)
    for _, node in scored:
        if len(result) >= max_count:
            break
        result.add(node)
    if not result and scored:
        result.add(scored[0][1])
    return result


def assign_roles(case: CaseGraph, metrics: GraphMetrics) -> dict[str, NodeAssessment]:
    victims = _victims(case, metrics)
    mules = _mules(case, metrics, victims)
    operators = _operators(case, metrics, victims)
    recruiters = _recruiters(case, metrics, mules, victims)
    kingpins = _kingpins(case, metrics, victims | mules)

    roles: dict[str, str] = {}
    for node in victims:
        roles[node] = ROLE_VICTIM
    for node in recruiters:
        roles[node] = ROLE_RECRUITER
    for node in mules:
        roles[node] = ROLE_MULE
    for node in operators:
        roles[node] = ROLE_OPERATOR
    for node in kingpins:
        roles[node] = ROLE_KINGPIN

    _propagate_person_roles(case, roles)

    tiers = _mule_tiers(metrics, roles, kingpins)
    assessments: dict[str, NodeAssessment] = {}
    for node, role in roles.items():
        metric = metrics.nodes.get(node)
        assessments[node] = _assess(node, role, metric, tiers.get(node, 0))
    for node, metric in metrics.nodes.items():
        if node not in assessments:
            assessments[node] = _assess(node, ROLE_UNKNOWN, metric, 0)
    return assessments


def _propagate_person_roles(case: CaseGraph, roles: dict[str, str]) -> None:
    for rel in case.relations.values():
        if rel.rtype != "owns":
            continue
        src_role = roles.get(rel.src)
        dst_role = roles.get(rel.dst)
        if src_role and not dst_role and rel.dst.startswith("person:"):
            roles[rel.dst] = src_role
        if dst_role and not src_role and rel.src.startswith("person:"):
            roles[rel.src] = dst_role
    for entity in case.entities.values():
        if entity.etype != EntityType.PERSON:
            continue
        for label in (ROLE_KINGPIN, ROLE_OPERATOR, ROLE_RECRUITER, ROLE_MULE, ROLE_VICTIM):
            if label in entity.labels:
                roles.setdefault(entity.id, label)


def _mule_tiers(metrics: GraphMetrics, roles: dict[str, str], kingpins: set[str]) -> dict[str, int]:
    mule_nodes = {node for node, role in roles.items() if role == ROLE_MULE}
    if not mule_nodes:
        return {}
    sinks = kingpins or set()
    dist: dict[str, int] = {}
    if sinks:
        dist = hop_distance(metrics.flow_graph, sinks, max_hops=8, reverse=True)
    tiers: dict[str, int] = {}
    for node in mule_nodes:
        hops = dist.get(node)
        if hops is None:
            tiers[node] = 0
        else:
            tiers[node] = max(1, hops)
    return tiers


def _assess(node: str, role: str, metric: NodeMetrics | None, tier: int) -> NodeAssessment:
    reasons: list[str] = []
    metric = metric or NodeMetrics(node_id=node)
    if role == ROLE_KINGPIN:
        reasons.append(f"terminal beneficiary: net inflow Rs.{metric.net_amount:,.0f}")
        if metric.pagerank:
            reasons.append(f"PageRank {metric.pagerank:.4f} among top nodes")
        if metric.in_deg:
            reasons.append(f"receives from {metric.in_deg} distinct parties")
    elif role == ROLE_MULE:
        reasons.append(
            f"pass-through: forwarded {metric.pass_through * 100:.0f}% of Rs.{metric.in_amount:,.0f} inflow"
        )
        if tier:
            reasons.append(f"layer position: Tier-{tier} (hops from cash-out = {tier})")
    elif role == ROLE_VICTIM:
        if metric.narrative_loss:
            reasons.append(f"loss of Rs.{metric.narrative_loss:,.0f} stated in the narrative")
        if metric.out_amount:
            reasons.append(f"outflow Rs.{metric.out_amount:,.0f} with no inbound credit (source of funds)")
        if not metric.narrative_loss and not metric.out_amount:
            reasons.append("named as a victim/loss-sufferer in the intelligence narrative")
    elif role == ROLE_OPERATOR:
        reasons.append("controls multiple SIM/device identities (telecom-side actor)")
    elif role == ROLE_RECRUITER:
        reasons.append("bridges multiple mule identities (recruitment/onboarding link)")
    if metric.labels:
        reasons.append("corroborated by narrative markers: " + ", ".join(metric.labels))
    return NodeAssessment(
        node_id=node,
        role=role,
        tier=tier,
        risk=0.0,
        reasons=reasons,
        metrics={
            "in_amount": metric.in_amount,
            "out_amount": metric.out_amount,
            "in_deg": metric.in_deg,
            "out_deg": metric.out_deg,
            "pass_through": metric.pass_through,
            "pagerank": metric.pagerank,
            "betweenness": metric.betweenness,
        },
    )


def build_hierarchy(case: CaseGraph, assessments: dict[str, NodeAssessment]) -> dict[str, list[str]]:
    hierarchy: dict[str, list[str]] = {
        ROLE_KINGPIN: [],
        ROLE_OPERATOR: [],
        ROLE_RECRUITER: [],
        ROLE_MULE: [],
        ROLE_VICTIM: [],
        ROLE_UNKNOWN: [],
    }
    for node, assessment in assessments.items():
        hierarchy.setdefault(assessment.role, []).append(node)
    for role, members in hierarchy.items():
        hierarchy[role] = sorted(
            members,
            key=lambda n: (-assessments[n].risk, -assessments[n].metrics.get("in_amount", 0.0), n),
        )
    return hierarchy


def summarize_roles(assessments: dict[str, NodeAssessment]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for assessment in assessments.values():
        counts[assessment.role] = counts.get(assessment.role, 0) + 1
    return counts


def iter_role(assessments: dict[str, NodeAssessment], role: str) -> Iterable[NodeAssessment]:
    return (a for a in assessments.values() if a.role == role)

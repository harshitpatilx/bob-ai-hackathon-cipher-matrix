from __future__ import annotations

from cfna.analysis.metrics import GraphMetrics
from cfna.models import (
    ROLE_KINGPIN,
    ROLE_MULE,
    ROLE_OPERATOR,
    ROLE_RECRUITER,
    ROLE_UNKNOWN,
    ROLE_VICTIM,
    CaseGraph,
    NodeAssessment,
)

ROLE_WEIGHT = {
    ROLE_KINGPIN: 40.0,
    ROLE_OPERATOR: 34.0,
    ROLE_RECRUITER: 30.0,
    ROLE_MULE: 26.0,
    ROLE_UNKNOWN: 14.0,
    ROLE_VICTIM: 0.0,
}

SUSPICIOUS_TERMS = [
    "otp", "sim swap", "ported", "phishing", "vishing", "mule", "rented",
    "blackmail", "obscene", "fake", "forged", "cloned", "duplicate",
]


def score_risk(
    case: CaseGraph,
    metrics: GraphMetrics,
    assessments: dict[str, NodeAssessment],
) -> None:
    max_pr = max((m.pagerank for m in metrics.nodes.values()), default=0.0) or 1.0
    max_in = max((m.in_amount for m in metrics.nodes.values()), default=0.0) or 1.0
    max_bc = max((m.betweenness for m in metrics.nodes.values()), default=0.0) or 1.0
    max_out = max((m.out_amount for m in metrics.nodes.values()), default=0.0) or 1.0

    for node, assessment in assessments.items():
        metric = metrics.nodes.get(node)
        if metric is None:
            assessment.risk = 5.0
            continue
        if assessment.role == ROLE_VICTIM:
            assessment.risk = 2.0
            continue
        score = ROLE_WEIGHT.get(assessment.role, 10.0)
        score += 18.0 * (metric.in_amount / max_in) if assessment.role != ROLE_VICTIM else 0.0
        score += 12.0 * (metric.out_amount / max_out) if assessment.role in {ROLE_MULE, ROLE_OPERATOR} else 0.0
        score += 14.0 * (metric.pagerank / max_pr)
        score += 8.0 * (metric.betweenness / max_bc)
        score += 6.0 * min(1.0, metric.degree / 10.0)
        hits = [term for term in SUSPICIOUS_TERMS if term in (metric.labels or [])]
        ent = case.entities.get(node)
        if ent:
            text_blob = " ".join(ent.labels + [str(v) for v in ent.attrs.values()]).lower()
            hits += [term for term in SUSPICIOUS_TERMS if term in text_blob]
        if hits:
            score += 5.0
            if "suspicious markers" not in " ".join(assessment.reasons):
                assessment.reasons.append("suspicious markers: " + ", ".join(sorted(set(hits))[:5]))
        assessment.risk = round(min(99.0, score), 1)


def top_risk(assessments: dict[str, NodeAssessment], limit: int = 10) -> list[NodeAssessment]:
    return sorted(assessments.values(), key=lambda a: a.risk, reverse=True)[:limit]

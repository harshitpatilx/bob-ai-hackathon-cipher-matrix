from __future__ import annotations

from typing import Any

from cfna import config as cfg
from cfna.analysis.evidence import _short
from cfna.analysis.hierarchy import summarize_roles
from cfna.analysis.metrics import GraphMetrics
from cfna.analysis.timeline import burst_windows, first_last
from cfna.models import CaseBrief, CaseGraph, PatternMatch, NodeAssessment

BOB_BACKEND: str = cfg.BOB_BACKEND_LABEL
IBM_BOB_ENDPOINT: str | None = None
IBM_BOB_CREDIT_COST = 0


class BobAgent:
    """Bob: investigation reasoning layer.

    Local deterministic backend today. IBM Bob API (metered on bob coins) can be
    plugged in later by setting IBM_BOB_ENDPOINT and implementing `external_reason`.
    """

    def __init__(self, backend: str = BOB_BACKEND) -> None:
        self.backend = backend
        self.calls_made = 0
        self.credits_spent = 0

    def external_reason(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        if not IBM_BOB_ENDPOINT:
            return None
        raise NotImplementedError(
            "IBM Bob endpoint not wired yet; supply IBM_BOB_ENDPOINT and bob-coin credentials."
        )

    def reason(
        self,
        case: CaseGraph,
        metrics: GraphMetrics,
        patterns: list[PatternMatch],
        assessments: dict[str, NodeAssessment],
        timeline: list[Any],
    ) -> dict[str, Any]:
        insights = self._insights(case, metrics, patterns, assessments, timeline)
        gaps = self._gaps(case, metrics, patterns, assessments, timeline)
        actions = self._actions(patterns)
        external = self.external_reason({"case_id": case.meta.case_id})
        if external:
            insights.extend(external.get("insights", []))
            gaps.extend(external.get("gaps", []))
        return {"insights": insights, "gaps": gaps, "actions": actions, "backend": self.backend}

    def _insights(
        self,
        case: CaseGraph,
        metrics: GraphMetrics,
        patterns: list[PatternMatch],
        assessments: dict[str, NodeAssessment],
        timeline: list[Any],
    ) -> list[str]:
        out: list[str] = []
        primary = patterns[0] if patterns else None
        if primary:
            confidence = int(round(primary.score * 100))
            out.append(
                f"Pattern verdict: {primary.name} (confidence {confidence}%). "
                + (primary.signals[0] if primary.signals else primary.summary)
            )
            if len(patterns) > 1 and patterns[1].score > 0.4:
                out.append(
                    f"Secondary pattern {patterns[1].name} scores {int(round(patterns[1].score * 100))}% - "
                    "investigate as a compound modality (same syndicate, different lure)."
                )

        roles = summarize_roles(assessments)
        out.append(
            f"Network shape: {len(metrics.full_graph.nodes)} entities, "
            f"{len(case.relation_list())} relationships across {len(metrics.components)} connected component(s); "
            f"documented money trail Rs.{metrics.total_flow:,.0f}."
        )

        kingpins = [a for a in assessments.values() if a.role == "kingpin"]
        mules = [a for a in assessments.values() if a.role == "mule"]
        operators = [a for a in assessments.values() if a.role == "operator"]
        victims = [a for a in assessments.values() if a.role == "victim"]
        if kingpins:
            top = sorted(kingpins, key=lambda a: -a.risk)[0]
            out.append(
                f"Hierarchy: {len(kingpins)} kingpin node(s), {len(operators)} operator(s), "
                f"{len(mules)} mule account(s) in {len({a.tier for a in mules})} layer(s), {len(victims)} victim node(s). "
                f"Primary beneficiary {_short(top.node_id)} (risk {top.risk}/99)."
            )
        tiers: dict[int, int] = {}
        for mule in mules:
            tiers[mule.tier] = tiers.get(mule.tier, 0) + 1
        if tiers:
            layer_text = ", ".join(f"Tier-{t}: {n}" for t, n in sorted(tiers.items()))
            out.append(f"Layering map: {layer_text}. Layers closer to Tier-1 are closest to cash-out.")

        if victims:
            loss = sum(m.loss_amount for m in metrics.nodes.values() if assessments.get(m.node_id) and assessments[m.node_id].role == "victim")
            out.append(f"Victim loss quantified at Rs.{loss:,.0f} across {len(victims)} victim identifiers - use as the 'property' line in the FIR.")

        first, last = first_last(timeline)
        if first:
            out.append(f"Time window of recorded activity: {first} to {last}.")
        bursts = burst_windows(timeline)
        if bursts:
            biggest = max(bursts, key=lambda b: b["count"])
            out.append(
                f"{len(bursts)} rapid-fire transfer burst(s) detected; biggest has {biggest['count']} transfers "
                f"worth Rs.{biggest['amount']:,.0f} inside {biggest['window_minutes']} minutes - indicates automated layering."
            )

        swap_rows = [r for r in _evidence_sim_sims(case)]
        if swap_rows:
            out.append(
                f"Telecom evidence: {len(swap_rows)} SIM(s) bound to multiple MSISDNs / re-issued - "
                "seize swap and porting logs from the operator before they age out."
            )

        risky = sorted(assessments.values(), key=lambda a: -a.risk)[:3]
        if risky:
            out.append(
                "Priority interrogations: "
                + "; ".join(f"{_short(a.node_id)} ({a.role}, risk {a.risk})" for a in risky)
                + "."
            )
        out.append(
            f"Bob scored {len(metrics.nodes)} identifiers and {len(case.relation_list())} edges using backend "
            f"'{self.backend}' (0 bob-coin calls so far; IBM Bob hook available for narrative expansion)."
        )
        return out

    def _gaps(
        self,
        case: CaseGraph,
        metrics: GraphMetrics,
        patterns: list[PatternMatch],
        assessments: dict[str, NodeAssessment],
        timeline: list[Any],
    ) -> list[str]:
        gaps: list[str] = []
        if patterns and patterns[0].score < 0.5:
            gaps.append(
                f"Primary pattern confidence is only {int(patterns[0].score * 100)}% - collect victim statements "
                "and operator KYC to firm up the modality."
            )
        weak = sum(1 for rel in case.relation_list() if rel.rtype == "co_occur")
        strong = sum(1 for rel in case.relation_list() if rel.rtype not in {"co_occur"})
        if weak > strong:
            gaps.append(
                f"{weak} of {len(case.relation_list())} links are weak co-occurrence only; convert them to "
                "CDR/transaction-proven links before filing."
            )
        no_dates = [rel for rel in case.relation_list() if rel.rtype == "transfer" and not rel.first_ts]
        if no_dates:
            gaps.append(f"{len(no_dates)} transfer(s) lack timestamps - pull certified statements with value dates.")
        without_kyc = [
            row for row in _account_rows(case, metrics, assessments)
            if row["role"] in {"kingpin", "operator", "recruiter", "mule"} and not row["bank"]
        ]
        if without_kyc:
            gaps.append(
                f"{len(without_kyc)} suspicious account(s) have no bank/IFSC on record - issue s.91 notices for KYC extraction."
            )
        phones_without_device = [
            e.id for e in case.entities.values()
            if e.etype.value == "phone" and not _has_device(case, e.id)
        ]
        if phones_without_device:
            gaps.append(
                f"{len(phones_without_device)} MSISDN(s) have no device mapping - request HLR/IMEI mapping from operators."
            )
        if not timeline:
            gaps.append("No timestamps recovered - the FIR timeline annexure cannot be built yet.")
        return gaps

    def _actions(self, patterns: list[PatternMatch]) -> list[str]:
        actions: list[str] = []
        if patterns:
            actions.extend(patterns[0].actions)
        for extra in patterns[1:3]:
            for action in extra.actions:
                if action not in actions:
                    actions.append(action)
        actions.extend(cfg.ACTIONS_COMMON)
        seen: set[str] = set()
        ordered: list[str] = []
        for action in actions:
            if action in seen:
                continue
            seen.add(action)
            ordered.append(action)
        return ordered


def _has_device(case: CaseGraph, phone_id: str) -> bool:
    for rel in case.relation_list():
        if rel.rtype in {"device_used_msisdn", "device_used_sim"} and rel.dst == phone_id:
            return True
    return False


def _evidence_sim_sims(case: CaseGraph) -> list[str]:
    per_sim: dict[str, set[str]] = {}
    for rel in case.relation_list():
        if rel.rtype == "sim_bound_to_msisdn":
            per_sim.setdefault(rel.src, set()).add(rel.dst)
    return [sim for sim, phones in per_sim.items() if len(phones) >= 2]


def _account_rows(
    case: CaseGraph,
    metrics: GraphMetrics,
    assessments: dict[str, NodeAssessment],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for node, metric in metrics.nodes.items():
        ent = case.entities.get(node)
        if ent is None or ent.etype.value not in {"account", "upi_id", "card"}:
            continue
        if metric.in_amount <= 0 and metric.out_amount <= 0:
            continue
        assessment = assessments.get(node)
        rows.append({"node": node, "bank": ent.attrs.get("bank", ""), "role": assessment.role if assessment else "unknown"})
    return rows

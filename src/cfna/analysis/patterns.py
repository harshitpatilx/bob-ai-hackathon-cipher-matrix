from __future__ import annotations

from dataclasses import dataclass, field

from cfna import config as cfg
from cfna.analysis.metrics import GraphMetrics
from cfna.models import CaseGraph, EntityType, PatternMatch


@dataclass
class PatternContext:
    case: CaseGraph
    metrics: GraphMetrics
    corpus: str
    keyword_hits: dict[str, list[str]] = field(default_factory=dict)


def build_context(case: CaseGraph, metrics: GraphMetrics) -> PatternContext:
    lines: list[str] = []
    for doc in case.documents:
        lines.extend(doc.lines)
    corpus = "\n".join(lines).lower()
    return PatternContext(case=case, metrics=metrics, corpus=corpus)


def _kw_score(ctx: PatternContext, keywords: list[str], pattern_id: str) -> tuple[float, list[str]]:
    hits = sorted({kw for kw in keywords if kw in ctx.corpus})
    ctx.keyword_hits[pattern_id] = hits
    if not hits:
        return 0.0, []
    score = min(1.0, len(hits) / 3.0)
    return score, [f"language markers matched: {', '.join(hits[:6])}"]


def _neighbors(ctx: PatternContext, node_id: str, rtypes: set[str], reverse: bool = False) -> set[str]:
    out: set[str] = set()
    for rel in ctx.case.relations.values():
        if rel.rtype not in rtypes:
            continue
        if not reverse and rel.src == node_id:
            out.add(rel.dst)
        elif reverse and rel.dst == node_id:
            out.add(rel.src)
    return out


def _signal_nodes(ctx: PatternContext, etypes: set[EntityType]) -> list[str]:
    return sorted(e.id for e in ctx.case.entities.values() if e.etype in etypes)


def structural_sim_swap(ctx: PatternContext) -> tuple[float, list[str]]:
    phones = _signal_nodes(ctx, {EntityType.PHONE})
    if not phones:
        return 0.0, []
    multi_device = []
    for phone in phones:
        devices = _neighbors(ctx, phone, {"device_used_msisdn", "device_used_sim"}, reverse=True)
        sims = _neighbors(ctx, phone, {"sim_bound_to_msisdn"}, reverse=True)
        if len(devices) >= 2 or len(sims) >= 2:
            multi_device.append(phone)
    multi_sim_devices = []
    for device in _signal_nodes(ctx, {EntityType.DEVICE}):
        sims = _neighbors(ctx, device, {"device_used_sim", "device_used_msisdn"}, reverse=False)
        if len(sims) >= 3:
            multi_sim_devices.append(device)
    activations = [
        e for e in ctx.case.entities.values()
        if e.etype == EntityType.SIM and e.attrs.get("activation_date")
    ]
    signals: list[str] = []
    ratio = len(multi_device) / max(1, len(phones))
    score = min(1.0, ratio * 2.2)
    if multi_device:
        signals.append(
            f"{len(multi_device)}/{len(phones)} MSISDNs seen on 2+ devices/SIMs - classic SIM-swap signature "
            f"(e.g. {', '.join(multi_device[:3])})"
        )
    if multi_sim_devices:
        score = min(1.0, score + 0.3)
        signals.append(f"{len(multi_sim_devices)} device(s) controlling 3+ SIMs: {', '.join(multi_sim_devices[:3])}")
    if activations:
        score = min(1.0, score + 0.2)
        signals.append(f"{len(activations)} SIM re-activation/porting records with dates on file")
    return score, signals


def structural_mule_chain(ctx: PatternContext) -> tuple[float, list[str]]:
    def is_mule(node: str) -> bool:
        metric = ctx.metrics.nodes.get(node)
        if metric is None or metric.in_amount < 5000:
            return False
        return metric.pass_through >= 0.85

    chain = ctx.metrics.flow_graph.longest_chain(is_mule)
    if len(chain) < 2:
        return 0.0, []
    depth = len(chain)
    score = min(1.0, max(0.0, (depth - 1) / 3.0))
    signals = [f"pass-through chain of {depth} hops: " + " -> ".join(_short(n) for n in chain[:6])]
    mule_count = sum(1 for n in ctx.metrics.nodes if is_mule(n))
    signals.append(f"{mule_count} accounts forward >=85% of inflow within the layer (mule behaviour)")
    return score, signals


def structural_many_to_few(ctx: PatternContext) -> tuple[float, list[str]]:
    collectors: list[tuple[str, int, float]] = []
    for node, metric in ctx.metrics.nodes.items():
        if metric.flow_in_deg >= 4 and metric.flow_out_deg >= 2 and metric.in_amount > 0:
            collectors.append((node, metric.flow_in_deg, metric.in_amount))
    if not collectors:
        return 0.0, []
    collectors.sort(key=lambda item: item[1], reverse=True)
    top = collectors[0]
    score = min(1.0, len(collectors) / 4.0)
    signals = [
        f"{len(collectors)} collector accounts with fan-in >=4 (e.g. {_short(top[0])} received from {top[1]} parties, "
        f"Rs.{top[2]:,.0f})"
    ]
    return score, signals


def structural_broadcast(ctx: PatternContext) -> tuple[float, list[str]]:
    best = None
    for node, metric in ctx.metrics.nodes.items():
        if not node.startswith("phone:"):
            continue
        if metric.call_out_deg >= 3 and metric.call_in_deg == 0:
            if best is None or metric.call_out_deg > best[1]:
                best = (node, metric.call_out_deg)
    if not best:
        return 0.0, []
    score = min(1.0, best[1] / 6.0)
    return score, [f"one-way broadcast number {_short(best[0])} contacted {best[1]} parties with no inbound calls"]


def structural_identity_mix(ctx: PatternContext) -> tuple[float, list[str]]:
    docs = [e for e in ctx.case.entities.values() if e.etype in {EntityType.PAN, EntityType.AADHAAR}]
    if not docs:
        return 0.0, []
    shared = 0
    for doc_ent in docs:
        linked = _neighbors(ctx, doc_ent.id, {"owns", "co_occur", "text_link", "sim_bound_to_msisdn"}, reverse=True)
        if len(linked) >= 2:
            shared += 1
    score = min(1.0, shared / 2.0) if shared else 0.3
    return score, [f"{len(docs)} identity documents in evidence, {shared} linked to multiple identifiers"]


def structural_cards(ctx: PatternContext) -> tuple[float, list[str]]:
    cards = _signal_nodes(ctx, {EntityType.CARD})
    if not cards:
        return 0.0, []
    return min(1.0, len(cards) / 3.0), [f"{len(cards)} card numbers recovered from evidence/records"]


def _short(node_id: str) -> str:
    return node_id.split(":", 1)[1][:22]


STRUCTURAL = {
    "SIM_SWAP_OTP": structural_sim_swap,
    "MULE_CHAIN": structural_mule_chain,
    "TASK_INVESTMENT_SCAM": structural_many_to_few,
    "PHISH_VISH": structural_broadcast,
    "LOAN_APP_EXTORTION": structural_many_to_few,
    "IDENTITY_KYC_FRAUD": structural_identity_mix,
    "CARD_CLONING": structural_cards,
    "SEXTORTION": lambda ctx: (0.0, []),
    "ROMANCE_HONEYTRAP": lambda ctx: (0.0, []),
}

KEYWORDS = {
    "SIM_SWAP_OTP": cfg.SIM_SWAP_KW,
    "MULE_CHAIN": ["mule", "rented account", "pass-through", "layering", "cash out", "withdrawn immediately", "benami"],
    "TASK_INVESTMENT_SCAM": cfg.TASK_KW,
    "PHISH_VISH": cfg.PHISH_KW,
    "LOAN_APP_EXTORTION": cfg.LOAN_KW,
    "IDENTITY_KYC_FRAUD": cfg.IDENTITY_KW,
    "CARD_CLONING": cfg.CARD_KW,
    "SEXTORTION": cfg.SEXTORTION_KW,
    "ROMANCE_HONEYTRAP": cfg.ROMANCE_KW,
}

WEIGHTS = {
    "SIM_SWAP_OTP": (0.4, 0.6),
    "MULE_CHAIN": (0.35, 0.65),
    "TASK_INVESTMENT_SCAM": (0.7, 0.3),
    "PHISH_VISH": (0.55, 0.45),
    "LOAN_APP_EXTORTION": (0.75, 0.25),
    "IDENTITY_KYC_FRAUD": (0.6, 0.4),
    "CARD_CLONING": (0.7, 0.3),
    "SEXTORTION": (1.0, 0.0),
    "ROMANCE_HONEYTRAP": (1.0, 0.0),
}


def classify_patterns(case: CaseGraph, metrics: GraphMetrics) -> list[PatternMatch]:
    ctx = build_context(case, metrics)
    matches: list[PatternMatch] = []
    for pattern_id in cfg.PATTERN_ORDER:
        kw_weight, struct_weight = WEIGHTS[pattern_id]
        kw, kw_signals = _kw_score(ctx, KEYWORDS[pattern_id], pattern_id)
        struct, struct_signals = STRUCTURAL[pattern_id](ctx)
        score = kw * kw_weight + struct * struct_weight
        if score <= 0.01:
            continue
        signals = struct_signals + kw_signals
        matches.append(
            PatternMatch(
                id=pattern_id,
                name=pattern_id.replace("_", " ").title(),
                score=round(min(1.0, score), 3),
                summary=cfg.PATTERN_SUMMARY[pattern_id],
                signals=signals,
                legal=list(cfg.LEGAL_BY_PATTERN.get(pattern_id, cfg.LEGAL_COMMON)),
                actions=list(cfg.ACTIONS_BY_PATTERN.get(pattern_id, [])),
            )
        )
    matches.sort(key=lambda m: m.score, reverse=True)
    if not matches and metrics.total_flow > 0:
        matches.append(
            PatternMatch(
                id="MULE_CHAIN",
                name="Mule Chain",
                score=0.3,
                summary=cfg.PATTERN_SUMMARY["MULE_CHAIN"],
                signals=["insufficient language markers; fund-flow alone indicates layered account abuse"],
                legal=list(cfg.LEGAL_BY_PATTERN["MULE_CHAIN"]),
                actions=list(cfg.ACTIONS_BY_PATTERN["MULE_CHAIN"]),
            )
        )
    return matches

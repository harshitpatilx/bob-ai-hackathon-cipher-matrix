from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable


class EntityType(str, Enum):
    UPI_ID = "upi_id"
    PHONE = "phone"
    SIM = "sim"
    DEVICE = "device"
    ACCOUNT = "account"
    IFSC = "ifsc"
    PERSON = "person"
    IP = "ip"
    EMAIL = "email"
    HANDLE = "handle"
    CARD = "card"
    AADHAAR = "aadhaar"
    PAN = "pan"
    LOCATION = "location"
    VEHICLE = "vehicle"


GRAPH_TYPES: set[EntityType] = {
    EntityType.UPI_ID,
    EntityType.PHONE,
    EntityType.SIM,
    EntityType.DEVICE,
    EntityType.ACCOUNT,
    EntityType.PERSON,
    EntityType.IP,
    EntityType.EMAIL,
    EntityType.HANDLE,
    EntityType.CARD,
    EntityType.AADHAAR,
    EntityType.PAN,
    EntityType.LOCATION,
    EntityType.VEHICLE,
    EntityType.IFSC,
}

IDENTIFIER_TYPES: set[EntityType] = {
    EntityType.UPI_ID,
    EntityType.PHONE,
    EntityType.ACCOUNT,
    EntityType.CARD,
    EntityType.IFSC,
}

ROLE_KINGPIN = "kingpin"
ROLE_OPERATOR = "operator"
ROLE_RECRUITER = "recruiter"
ROLE_MULE = "mule"
ROLE_VICTIM = "victim"
ROLE_UNKNOWN = "unknown"

ROLE_ORDER = [ROLE_KINGPIN, ROLE_OPERATOR, ROLE_RECRUITER, ROLE_MULE, ROLE_VICTIM, ROLE_UNKNOWN]

ROLE_COLORS = {
    ROLE_KINGPIN: "#c62828",
    ROLE_OPERATOR: "#ef6c00",
    ROLE_RECRUITER: "#8e24aa",
    ROLE_MULE: "#f9a825",
    ROLE_VICTIM: "#1565c0",
    ROLE_UNKNOWN: "#78909c",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class Entity:
    etype: EntityType
    norm: str
    raw: str = ""
    labels: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    mentions: int = 1
    attrs: dict[str, Any] = field(default_factory=dict)

    @property
    def id(self) -> str:
        return f"{self.etype.value}:{self.norm}"

    def add_label(self, label: str) -> None:
        label = label.lower().strip()
        if label and label not in self.labels:
            self.labels.append(label)

    def add_source(self, source: str) -> None:
        if source and source not in self.sources:
            self.sources.append(source)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.etype.value,
            "value": self.norm,
            "raw": self.raw,
            "labels": list(self.labels),
            "sources": list(self.sources),
            "mentions": self.mentions,
            "attrs": dict(self.attrs),
        }


@dataclass
class Relation:
    src: str
    dst: str
    rtype: str
    weight: float = 1.0
    amount: float = 0.0
    count: int = 1
    directed: bool = True
    evidence: list[str] = field(default_factory=list)
    first_ts: str = ""
    last_ts: str = ""
    sources: list[str] = field(default_factory=list)

    def merge(self, other: Relation) -> None:
        self.count += other.count
        self.weight = max(self.weight, other.weight) + (0.1 if other.amount else 0.0)
        self.amount += other.amount
        for item in other.evidence:
            if item and item not in self.evidence and len(self.evidence) < 8:
                self.evidence.append(item)
        for src in other.sources:
            if src not in self.sources:
                self.sources.append(src)
        if other.first_ts and (not self.first_ts or other.first_ts < self.first_ts):
            self.first_ts = other.first_ts
        if other.last_ts and (not self.last_ts or other.last_ts > self.last_ts):
            self.last_ts = other.last_ts

    def to_dict(self) -> dict[str, Any]:
        return {
            "src": self.src,
            "dst": self.dst,
            "type": self.rtype,
            "weight": round(self.weight, 3),
            "amount": round(self.amount, 2),
            "count": self.count,
            "directed": self.directed,
            "evidence": list(self.evidence),
            "first_ts": self.first_ts,
            "last_ts": self.last_ts,
            "sources": list(self.sources),
        }


@dataclass
class Document:
    path: str
    kind: str
    text: str
    lines: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "kind": self.kind, "chars": len(self.text), "lines": len(self.lines)}


@dataclass
class CaseMeta:
    case_id: str = "case"
    title: str = "Cyber Fraud Case"
    police_station: str = ""
    district: str = ""
    state: str = ""
    complainant: str = ""
    occurred_on: str = ""
    reported_on: str = ""
    officer: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "title": self.title,
            "police_station": self.police_station,
            "district": self.district,
            "state": self.state,
            "complainant": self.complainant,
            "occurred_on": self.occurred_on,
            "reported_on": self.reported_on,
            "officer": self.officer,
            "notes": self.notes,
        }


@dataclass
class CaseGraph:
    meta: CaseMeta = field(default_factory=CaseMeta)
    entities: dict[str, Entity] = field(default_factory=dict)
    relations: dict[tuple[str, str, str], Relation] = field(default_factory=dict)
    documents: list[Document] = field(default_factory=list)
    records: list[dict[str, Any]] = field(default_factory=list)

    def add_entity(
        self,
        etype: EntityType,
        norm: str,
        raw: str | None = None,
        source: str = "",
        label: str = "",
        attrs: dict[str, Any] | None = None,
    ) -> Entity:
        norm = norm.strip()
        entity = self.entities.get(f"{etype.value}:{norm}")
        if entity is None:
            entity = Entity(etype=etype, norm=norm, raw=raw or norm)
            self.entities[entity.id] = entity
        elif raw and (not entity.raw or len(raw) > len(entity.raw)):
            entity.raw = raw
        entity.mentions += 1
        entity.add_source(source)
        if label:
            entity.add_label(label)
        if attrs:
            entity.attrs.update({k: v for k, v in attrs.items() if v not in (None, "")})
        return entity

    def add_relation(
        self,
        src: str,
        dst: str,
        rtype: str,
        weight: float = 1.0,
        amount: float = 0.0,
        directed: bool = True,
        evidence: str = "",
        ts: str = "",
        source: str = "",
    ) -> Relation:
        key = (src, dst, rtype)
        rel = self.relations.get(key)
        incoming = Relation(
            src=src,
            dst=dst,
            rtype=rtype,
            weight=weight,
            amount=amount,
            count=1,
            directed=directed,
            evidence=[evidence] if evidence else [],
            first_ts=ts,
            last_ts=ts,
            sources=[source] if source else [],
        )
        if rel is None:
            self.relations[key] = incoming
            return incoming
        rel.merge(incoming)
        return rel

    def get(self, entity_id: str) -> Entity | None:
        return self.entities.get(entity_id)

    def of_types(self, *types: EntityType) -> list[Entity]:
        wanted = set(types)
        return [e for e in self.entities.values() if e.etype in wanted]

    def relation_list(self) -> list[Relation]:
        return list(self.relations.values())

    def stats(self) -> dict[str, Any]:
        by_type: dict[str, int] = {}
        for ent in self.entities.values():
            by_type[ent.etype.value] = by_type.get(ent.etype.value, 0) + 1
        by_rel: dict[str, int] = {}
        for rel in self.relations.values():
            by_rel[rel.rtype] = by_rel.get(rel.rtype, 0) + 1
        total_amount = sum(r.amount for r in self.relations.values())
        return {
            "entities": len(self.entities),
            "relations": len(self.relations),
            "documents": len(self.documents),
            "records": len(self.records),
            "entity_types": dict(sorted(by_type.items())),
            "relation_types": dict(sorted(by_rel.items())),
            "total_trail_amount": round(total_amount, 2),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "meta": self.meta.to_dict(),
            "stats": self.stats(),
            "entities": [e.to_dict() for e in self.entities.values()],
            "relations": [r.to_dict() for r in self.relations.values()],
            "documents": [d.to_dict() for d in self.documents],
        }

    def ids(self) -> Iterable[str]:
        return self.entities.keys()


@dataclass
class PatternMatch:
    id: str
    name: str
    score: float
    summary: str
    signals: list[str] = field(default_factory=list)
    legal: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "score": round(self.score, 3),
            "summary": self.summary,
            "signals": list(self.signals),
            "legal": list(self.legal),
            "actions": list(self.actions),
        }


@dataclass
class NodeAssessment:
    node_id: str
    role: str
    tier: int = 0
    risk: float = 0.0
    reasons: list[str] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "role": self.role,
            "tier": self.tier,
            "risk": round(self.risk, 1),
            "reasons": list(self.reasons),
            "metrics": {k: round(v, 3) for k, v in self.metrics.items()},
        }


@dataclass
class TimelineEvent:
    ts: str
    etype: str
    summary: str
    amount: float = 0.0
    ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ts": self.ts,
            "etype": self.etype,
            "summary": self.summary,
            "amount": round(self.amount, 2),
            "ref": self.ref,
        }


@dataclass
class CaseBrief:
    meta: CaseMeta
    generated_at: str
    patterns: list[PatternMatch] = field(default_factory=list)
    assessments: dict[str, NodeAssessment] = field(default_factory=dict)
    hierarchy: dict[str, list[str]] = field(default_factory=dict)
    timeline: list[TimelineEvent] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)
    insights: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    evidence: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    actions: list[str] = field(default_factory=list)
    legal: list[str] = field(default_factory=list)

    @property
    def primary(self) -> PatternMatch | None:
        return self.patterns[0] if self.patterns else None

    def role_members(self, role: str) -> list[NodeAssessment]:
        return [a for a in self.assessments.values() if a.role == role]

    def to_dict(self) -> dict[str, Any]:
        return {
            "meta": self.meta.to_dict(),
            "generated_at": self.generated_at,
            "patterns": [p.to_dict() for p in self.patterns],
            "assessments": [a.to_dict() for a in self.assessments.values()],
            "hierarchy": self.hierarchy,
            "timeline": [e.to_dict() for e in self.timeline],
            "stats": self.stats,
            "insights": self.insights,
            "gaps": self.gaps,
            "evidence": self.evidence,
            "actions": self.actions,
            "legal": self.legal,
        }

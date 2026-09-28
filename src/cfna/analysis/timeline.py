from __future__ import annotations

from datetime import datetime
from typing import Any

from cfna.models import CaseGraph, CaseMeta, TimelineEvent

MAX_EVENTS = 400


def _parse(ts: str) -> str:
    ts = ts.strip()
    if not ts:
        return "9999-12-31 00:00:00"
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(ts, fmt).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return ts


def build_timeline(case: CaseGraph) -> list[TimelineEvent]:
    events: list[TimelineEvent] = []

    for rel in case.relation_list():
        if not rel.first_ts:
            continue
        ts = _parse(rel.first_ts)
        if rel.rtype == "transfer":
            src = rel.src.split(":", 1)[1][:24]
            dst = rel.dst.split(":", 1)[1][:24]
            events.append(
                TimelineEvent(
                    ts=ts,
                    etype="transfer",
                    summary=f"Rs.{rel.amount:,.0f} moved {src} -> {dst}",
                    amount=rel.amount,
                    ref=rel.src,
                )
            )
        elif rel.rtype == "call":
            events.append(
                TimelineEvent(
                    ts=ts,
                    etype="call",
                    summary=f"Call {rel.src.split(':', 1)[1]} -> {rel.dst.split(':', 1)[1]} ({rel.count}x)",
                    ref=rel.src,
                )
            )
        elif rel.rtype == "sim_bound_to_msisdn":
            events.append(
                TimelineEvent(
                    ts=ts,
                    etype="sim_event",
                    summary=f"SIM {rel.src.split(':', 1)[1][:20]} bound to {rel.dst.split(':', 1)[1]}",
                    ref=rel.src,
                )
            )

    for entity in case.entities.values():
        activation = str(entity.attrs.get("activation_date") or "")
        if activation and entity.etype.value == "sim":
            events.append(
                TimelineEvent(
                    ts=_parse(activation),
                    etype="sim_activation",
                    summary=f"SIM {entity.norm[:20]} activated/re-issued",
                    ref=entity.id,
                )
            )

    meta = case.meta
    if meta.occurred_on:
        events.append(TimelineEvent(ts=_parse(meta.occurred_on), etype="offence", summary="offence reported to have occurred", ref="meta"))
    if meta.reported_on:
        events.append(TimelineEvent(ts=_parse(meta.reported_on), etype="report", summary="complaint/FIR lodged", ref="meta"))

    events.sort(key=lambda e: e.ts)
    return events[:MAX_EVENTS]


def burst_windows(events: list[TimelineEvent], minutes: int = 15, min_count: int = 4) -> list[dict[str, Any]]:
    transfers = [e for e in events if e.etype == "transfer" and e.ts != "9999-12-31 00:00:00"]
    bursts: list[dict[str, Any]] = []
    current: list[TimelineEvent] = []

    def flush() -> None:
        if len(current) >= min_count:
            total = sum(e.amount for e in current)
            bursts.append(
                {
                    "start": current[0].ts,
                    "end": current[-1].ts,
                    "count": len(current),
                    "amount": round(total, 2),
                    "window_minutes": minutes,
                }
            )

    for event in transfers:
        if not current:
            current = [event]
            continue
        try:
            t0 = datetime.strptime(current[-1].ts, "%Y-%m-%d %H:%M:%S")
            t1 = datetime.strptime(event.ts, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            current = [event]
            continue
        if (t1 - t0).total_seconds() <= minutes * 60:
            current.append(event)
        else:
            flush()
            current = [event]
    flush()
    return bursts


def first_last(events: list[TimelineEvent]) -> tuple[str, str]:
    real = [e for e in events if e.ts != "9999-12-31 00:00:00"]
    if not real:
        return "", ""
    return real[0].ts, real[-1].ts

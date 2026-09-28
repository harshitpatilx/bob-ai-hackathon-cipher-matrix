from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from cfna import config as cfg
from cfna.models import CaseGraph, Document, Entity, EntityType

PSP_PATTERN = re.compile(r"^[a-z0-9._-]{2,64}@([a-z]{2,32})$", re.I)
VEHICLE_RE = re.compile(r"\b([A-Z]{2}\d{2}[A-Z]{1,3}\d{4})\b")


@dataclass(order=True)
class Span:
    priority: int
    start: int
    end: int
    etype: EntityType = field(compare=False)
    value: str = field(compare=False)
    norm: str = field(compare=False)
    raw: str = field(compare=False)


def _upi_valid(value: str) -> bool:
    match = PSP_PATTERN.match(value.strip())
    if not match:
        return False
    domain = match.group(1).lower()
    local = value.split("@", 1)[0]
    if domain in cfg.UPI_PSP:
        return True
    return bool(re.fullmatch(r"\d{8,12}", local))


def _norm_for(etype: EntityType, raw: str) -> str:
    if etype == EntityType.PHONE:
        return cfg.normalize_phone(raw)
    if etype == EntityType.UPI_ID:
        return cfg.normalize_upi(raw)
    if etype == EntityType.HANDLE:
        return cfg.normalize_handle(raw)
    if etype in (EntityType.ACCOUNT, EntityType.DEVICE, EntityType.SIM, EntityType.CARD):
        return cfg.normalize_account(raw)
    if etype == EntityType.IFSC:
        return cfg.normalize_ifsc(raw)
    if etype in (EntityType.PAN, EntityType.LOCATION, EntityType.VEHICLE):
        return raw.strip().upper()
    if etype == EntityType.IP:
        return raw.strip()
    if etype == EntityType.EMAIL:
        return raw.strip().lower()
    return raw.strip()


MATCHERS: list[tuple[int, re.Pattern[str], EntityType, Callable[[str], bool] | None]] = [
    (100, cfg.EMAIL_RE, EntityType.EMAIL, None),
    (95, cfg.UPI_RE, EntityType.UPI_ID, _upi_valid),
    (90, cfg.ICCID_RE, EntityType.SIM, None),
    (88, cfg.IMEI_RE, EntityType.DEVICE, None),
    (86, cfg.PAN_RE, EntityType.PAN, None),
    (84, cfg.AADHAAR_RE, EntityType.AADHAAR, None),
    (82, cfg.CARD_RE, EntityType.CARD, None),
    (80, cfg.IFSC_RE, EntityType.IFSC, None),
    (76, cfg.PHONE_RE, EntityType.PHONE, lambda v: len(cfg.normalize_phone(v)) == 10),
    (74, VEHICLE_RE, EntityType.VEHICLE, None),
    (70, cfg.IPV4_RE, EntityType.IP, None),
    (60, cfg.HANDLE_RE, EntityType.HANDLE, None),
    (50, cfg.ACCOUNT_RE, EntityType.ACCOUNT, None),
]

NAME_HINT_TYPES = (EntityType.ACCOUNT, EntityType.UPI_ID, EntityType.PHONE, EntityType.PERSON)


def find_spans(text: str) -> list[Span]:
    candidates: list[Span] = []
    for priority, pattern, etype, validator in MATCHERS:
        for match in pattern.finditer(text):
            raw = match.group(1)
            if validator is not None and not validator(raw):
                continue
            norm = _norm_for(etype, raw)
            if etype == EntityType.HANDLE and (norm.isdigit() or len(norm) < 4):
                continue
            if etype in (EntityType.DEVICE, EntityType.SIM, EntityType.ACCOUNT, EntityType.CARD) and len(norm) < 9:
                continue
            if etype == EntityType.DEVICE and not (14 <= len(norm) <= 16):
                continue
            if etype == EntityType.SIM and not (18 <= len(norm) <= 22):
                continue
            if etype == EntityType.IFSC and norm[4] != "0":
                continue
            if etype == EntityType.IP and any(int(p) > 255 for p in norm.split(".")):
                continue
            start, end = match.span(1)
            candidates.append(Span(-priority, start, end, etype, raw, norm, raw))

    candidates.sort(key=lambda s: (s.start, s.priority))

    accepted: list[Span] = []
    for span in candidates:
        if accepted and span.start < accepted[-1].end:
            if span.priority < accepted[-1].priority:
                accepted[-1] = span
            continue
        accepted.append(span)
    accepted.sort(key=lambda s: s.start)
    return accepted


def extract_name_spans(text: str) -> list[tuple[int, int, str]]:
    spans: list[tuple[int, int, str]] = []
    for pattern in (cfg.NAME_AFTER_RE, cfg.DISTRICT_RE):
        for match in pattern.finditer(text):
            name = match.group(1).strip()
            first = name.split()[0].lower()
            if first in cfg.NAME_STOPWORDS:
                continue
            if len(name.split()) < 2:
                continue
            spans.append((match.start(1), match.end(1), name))
    spans.sort()
    return spans


def extract_names(text: str) -> list[str]:
    return [name for _, _, name in extract_name_spans(text)]


ROLE_TARGET_VALUES = {
    etype.value
    for etype in (
        EntityType.PERSON,
        EntityType.ACCOUNT,
        EntityType.UPI_ID,
        EntityType.PHONE,
        EntityType.CARD,
        EntityType.HANDLE,
        EntityType.EMAIL,
    )
}
FORWARD_WINDOW = 60
BACKWARD_WINDOW = 25


def nearest_entity(located: list[tuple[int, int, str]], pos: int, window: int = 160) -> str | None:
    """Entity whose span sits closest to `pos`, preferring the one following it."""
    best: tuple[int, int, str] | None = None  # (distance, side, entity)
    for start, end, ent_id in located:
        if start <= pos <= end:
            return ent_id
        distance = start - pos if start > pos else pos - end
        if distance > window:
            continue
        side = 0 if start >= pos else 1
        key = (distance, side)
        if best is None or key < (best[0], best[1]):
            best = (distance, side, ent_id)
    return best[2] if best else None


def _marker_target(located: list[tuple[int, int, str]], marker_start: int, marker_end: int) -> str | None:
    """Which entity a role marker actually names.

    "Kingpin Bhola Ram Rai ... holds account 5001000000001" -> the entity the marker introduces,
    i.e. the nearest one it *precedes* (within a short window). A trailing anaphoric mention
    ("... final layer before the kingpin") introduces nothing, so only a tightly attached entity
    right in front of the marker counts.
    """
    candidates = [(s, e, i) for s, e, i in located if i.split(":", 1)[0] in ROLE_TARGET_VALUES]
    forward = sorted((s - marker_end, i) for s, e, i in candidates if s >= marker_end and s - marker_end <= FORWARD_WINDOW)
    if forward:
        return forward[0][1]
    backward = sorted((marker_start - e, i) for s, e, i in candidates if e <= marker_start and marker_start - e <= BACKWARD_WINDOW)
    if backward:
        return backward[0][1]
    return None


def apply_role_labels(case: CaseGraph, line: str, located: list[tuple[int, int, str]]) -> set[str]:
    """Attach role markers to the entity they actually name, not to every entity in the sentence.

    `located` carries (start, end, entity_id) spans so "Kingpin Anup Saha ... victim Ramesh
    Kumar" labels only the entity next to each marker.
    """
    lowered = line.lower()
    applied: set[str] = set()
    for role, markers in cfg.ROLE_MARKERS.items():
        if role not in cfg.ROLE_LABEL_SET:
            continue
        for marker in markers:
            idx = lowered.find(marker)
            while idx != -1:
                hit = _marker_target(located, idx, idx + len(marker))
                if hit:
                    ent = case.entities.get(hit)
                    if ent is not None:
                        ent.add_label(role)
                        applied.add(hit)
                idx = lowered.find(marker, idx + len(marker))
    return applied


def propagate_owner_labels(case: CaseGraph) -> None:
    """A labelled owner's account/number inherits the label - downwards only.

    "Kingpin Anup Saha holds account 5001000000001" names the person; the money actually sits
    on the account, so the label has to travel down the `owns` edge. It never travels back up,
    and it never overwrites a different role already attached to the target: otherwise two people
    sharing one MSISDN (victim SIM re-issued to the operator) would smear every label onto every
    node in the component.
    """
    person_value = EntityType.PERSON.value
    for rel in case.relation_list():
        if rel.rtype != "owns":
            continue
        src_is_person = rel.src.split(":", 1)[0] == person_value
        dst_is_person = rel.dst.split(":", 1)[0] == person_value
        if src_is_person == dst_is_person:
            continue
        owner, target = (rel.src, rel.dst) if src_is_person else (rel.dst, rel.src)
        owner_ent = case.entities.get(owner)
        target_ent = case.entities.get(target)
        if owner_ent is None or target_ent is None:
            continue
        carried = [label for label in owner_ent.labels if label in cfg.ROLE_LABEL_SET]
        if not carried:
            continue
        held = {label for label in target_ent.labels if label in cfg.ROLE_LABEL_SET}
        for label in carried:
            if held and label not in held:
                continue
            target_ent.add_label(label)



def line_labels(line: str) -> list[str]:
    lowered = line.lower()
    labels: list[str] = []
    for role, markers in cfg.ROLE_MARKERS.items():
        if role == "accused":
            continue
        if any(marker in lowered for marker in markers):
            labels.append(role)
    if "accused" in lowered and not labels:
        labels.append("suspect")
    return labels


def extract_from_text(case: CaseGraph, doc: Document) -> None:
    for line in doc.lines:
        for sentence in cfg.SENTENCE_SPLIT.split(line):
            _extract_sentence(case, doc, sentence)


def _extract_sentence(case: CaseGraph, doc: Document, sentence: str) -> None:
    """Entities plus precise role labels for one sentence.

    Labels are resolved sentence-by-sentence: a marker in sentence 2 must never claim an entity
    introduced in sentence 5 of the same paragraph.
    """
    lowered = sentence.lower()
    role_seen = any(
        marker in lowered
        for role, markers in cfg.ROLE_MARKERS.items()
        if role in cfg.ROLE_LABEL_SET
        for marker in markers
    )
    spans = find_spans(sentence)
    located: list[tuple[int, int, str]] = []
    for span in spans:
        if span.etype not in (
            EntityType.UPI_ID,
            EntityType.PHONE,
            EntityType.ACCOUNT,
            EntityType.DEVICE,
            EntityType.SIM,
            EntityType.IFSC,
            EntityType.CARD,
            EntityType.EMAIL,
            EntityType.HANDLE,
            EntityType.IP,
            EntityType.PAN,
            EntityType.VEHICLE,
            EntityType.LOCATION,
        ):
            continue
        entity = case.add_entity(
            span.etype,
            span.norm,
            raw=span.raw,
            source=doc.path,
            label="",
        )
        located.append((span.start, span.end, entity.id))
    for start, end, name in extract_name_spans(sentence):
        entity = case.add_entity(EntityType.PERSON, name.upper(), raw=name, source=doc.path)
        located.append((start, end, entity.id))
    located.sort()
    if role_seen:
        apply_role_labels(case, sentence, located)
    elif "accused" in lowered or "suspect" in lowered:
        for _, _, entity_id in located:
            ent = case.entities.get(entity_id)
            if ent is not None:
                ent.add_label("suspect")


def ingest_records(case: CaseGraph, records: list[dict[str, Any]]) -> None:
    for row in records:
        kind = str(row.get("__kind", "records"))
        source = str(row.get("__source", "records"))
        case.records.append(dict(row))
        if kind == "transactions":
            _ingest_transaction(case, row, source)
        elif kind == "call_logs":
            _ingest_call(case, row, source)
        elif kind == "sim_registry":
            _ingest_sim(case, row, source)
        elif kind == "device_logs":
            _ingest_device(case, row, source)
        else:
            _ingest_generic(case, row, source)


def _pick(row: dict[str, Any], *names: str) -> str:
    lowered = {str(k).lower(): v for k, v in row.items() if not str(k).startswith("__")}
    for name in names:
        value = lowered.get(name.lower())
        if value not in (None, "", 0, "0"):
            return str(value).strip()
    return ""


def _ingest_transaction(case: CaseGraph, row: dict[str, Any], source: str) -> None:
    src_upi = _pick(row, "from_upi", "src_upi", "payer_upi", "payer_vpa")
    src_acc = _pick(row, "from_account", "src_account", "payer_account", "payer_acct")
    dst_upi = _pick(row, "to_upi", "dst_upi", "payee_upi", "payee_vpa")
    dst_acc = _pick(row, "to_account", "dst_account", "payee_account", "payee_acct")
    amount = float(_pick(row, "amount_inr", "amount") or 0)
    ts = _pick(row, "timestamp", "txn_time", "date", "datetime")
    txn_id = _pick(row, "txn_id", "id", "reference")
    remarks = _pick(row, "remarks", "narration", "note", "description")
    channel = _pick(row, "channel", "mode", "type")
    src_name = _pick(row, "from_name", "payer_name")
    dst_name = _pick(row, "to_name", "payee_name")
    src_bank = _pick(row, "from_bank", "src_bank", "payer_bank")
    dst_bank = _pick(row, "to_bank", "dst_bank", "payee_bank")

    src_id = ""
    if src_acc:
        ent = case.add_entity(EntityType.ACCOUNT, cfg.normalize_account(src_acc), raw=src_acc, source=source,
                              attrs={"bank": src_bank} if src_bank else None)
        src_id = ent.id
    if src_upi:
        ent = case.add_entity(EntityType.UPI_ID, cfg.normalize_upi(src_upi), raw=src_upi, source=source)
        if src_id:
            case.add_relation(ent.id, src_id, "maps_to", weight=1.0, source=source, ts=ts,
                              evidence=f"{src_upi} maps to a/c {src_acc or '-'}")
        else:
            src_id = ent.id
    if src_name:
        person = case.add_entity(EntityType.PERSON, src_name.upper(), raw=src_name, source=source)
        if src_id:
            case.add_relation(person.id, src_id, "owns", weight=1.2, source=source, ts=ts,
                              evidence=f"a/c {src_acc or src_upi} in name of {src_name}")

    dst_id = ""
    if dst_acc:
        ent = case.add_entity(EntityType.ACCOUNT, cfg.normalize_account(dst_acc), raw=dst_acc, source=source,
                              attrs={"bank": dst_bank} if dst_bank else None)
        dst_id = ent.id
    if dst_upi:
        ent = case.add_entity(EntityType.UPI_ID, cfg.normalize_upi(dst_upi), raw=dst_upi, source=source)
        if dst_id:
            case.add_relation(ent.id, dst_id, "maps_to", weight=1.0, source=source, ts=ts,
                              evidence=f"{dst_upi} maps to a/c {dst_acc or '-'}")
        else:
            dst_id = ent.id
    if dst_name:
        person = case.add_entity(EntityType.PERSON, dst_name.upper(), raw=dst_name, source=source)
        if dst_id:
            case.add_relation(person.id, dst_id, "owns", weight=1.2, source=source, ts=ts,
                              evidence=f"a/c {dst_acc or dst_upi} in name of {dst_name}")

    if src_id and dst_id and amount > 0:
        evidence = f"{txn_id or 'txn'}: Rs.{amount:,.2f} {src_id.split(':', 1)[1]} -> {dst_id.split(':', 1)[1]}"
        if remarks:
            evidence += f" [{remarks}]"
        case.add_relation(src_id, dst_id, "transfer", weight=1.0, amount=amount, ts=ts,
                          source=source, evidence=evidence)


def _ingest_call(case: CaseGraph, row: dict[str, Any], source: str) -> None:
    a = _pick(row, "msisdn_a", "src_msisdn", "caller", "from_msisdn", "a_msisdn")
    b = _pick(row, "msisdn_b", "dst_msisdn", "callee", "to_msisdn", "b_msisdn")
    imei_a = _pick(row, "imei_a", "src_imei", "caller_imei")
    imei_b = _pick(row, "imei_b", "dst_imei", "callee_imei")
    ts = _pick(row, "timestamp", "call_time", "date")
    duration = _pick(row, "duration_sec", "duration", "call_duration")
    call_id = _pick(row, "call_id", "id")
    cell = _pick(row, "cell_id", "cell_tower", "tower")

    a_id = b_id = ""
    if a:
        a_id = case.add_entity(EntityType.PHONE, cfg.normalize_phone(a), raw=a, source=source).id
    if b:
        b_id = case.add_entity(EntityType.PHONE, cfg.normalize_phone(b), raw=b, source=source).id
    if a_id and b_id:
        evidence = f"{call_id or 'CDR'}: {a} -> {b} ({duration or '0'}s)"
        if cell:
            evidence += f" tower {cell}"
        case.add_relation(a_id, b_id, "call", weight=1.0, ts=ts, source=source, evidence=evidence)
    if a_id and imei_a:
        dev = case.add_entity(EntityType.DEVICE, cfg.normalize_account(imei_a), raw=imei_a, source=source)
        case.add_relation(dev.id, a_id, "device_used_msisdn", weight=1.5, ts=ts, source=source,
                          evidence=f"MSISDN {a} used on IMEI {imei_a}")
    if b_id and imei_b:
        dev = case.add_entity(EntityType.DEVICE, cfg.normalize_account(imei_b), raw=imei_b, source=source)
        case.add_relation(dev.id, b_id, "device_used_msisdn", weight=1.5, ts=ts, source=source,
                          evidence=f"MSISDN {b} used on IMEI {imei_b}")


def _ingest_sim(case: CaseGraph, row: dict[str, Any], source: str) -> None:
    msisdn = _pick(row, "msisdn", "phone", "number", "sim_number")
    iccid = _pick(row, "iccid", "sim_no", "sim_serial", "sim_id")
    imei = _pick(row, "imei", "device_imei", "device")
    activated = _pick(row, "activation_date", "activation_ts", "activated_on", "date")
    status = _pick(row, "status", "sim_status")
    provider = _pick(row, "provider", "operator", "telco")
    district = _pick(row, "district", "place", "city")
    owner = _pick(row, "owner_name", "name", "subscriber", "accused_name")
    role_hint = _pick(row, "role", "remark", "remarks")

    labels = line_labels(role_hint) if role_hint else []
    sim_id = ""
    if iccid:
        attrs = {"activation_date": activated, "provider": provider, "status": status} if (activated or provider or status) else None
        sim_id = case.add_entity(EntityType.SIM, cfg.normalize_account(iccid), raw=iccid, source=source,
                                 label=labels[0] if labels else "", attrs=attrs).id
    phone_id = ""
    if msisdn:
        phone_id = case.add_entity(EntityType.PHONE, cfg.normalize_phone(msisdn), raw=msisdn, source=source,
                                   label=labels[0] if labels else "").id
    device_id = ""
    if imei:
        device_id = case.add_entity(EntityType.DEVICE, cfg.normalize_account(imei), raw=imei, source=source).id
    if sim_id and phone_id:
        case.add_relation(sim_id, phone_id, "sim_bound_to_msisdn", weight=2.0, ts=activated, source=source,
                          evidence=f"ICCID {iccid} bound to {msisdn} ({activated or 'date n/a'})")
    if device_id and sim_id:
        case.add_relation(device_id, sim_id, "device_used_sim", weight=2.0, ts=activated, source=source,
                          evidence=f"IMEI {imei} used SIM {iccid}")
    if device_id and phone_id:
        case.add_relation(device_id, phone_id, "device_used_msisdn", weight=2.0, ts=activated, source=source,
                          evidence=f"IMEI {imei} used MSISDN {msisdn}")
    if owner and phone_id:
        person = case.add_entity(EntityType.PERSON, owner.upper(), raw=owner, source=source,
                                 label=labels[0] if labels else "")
        case.add_relation(person.id, phone_id, "owns", weight=1.2, source=source, ts=activated,
                          evidence=f"SIM {iccid or msisdn} in name of {owner}")
        if sim_id:
            case.add_relation(person.id, sim_id, "owns", weight=1.2, source=source, ts=activated,
                              evidence=f"SIM {iccid} in name of {owner}")
    if district:
        loc = case.add_entity(EntityType.LOCATION, district.upper(), raw=district, source=source)
        anchor = sim_id or phone_id
        if anchor:
            case.add_relation(anchor, loc.id, "located_at", weight=0.5, source=source,
                              evidence=f"{iccid or msisdn} activated at {district}")
    for label in labels:
        for entity_id in {sim_id, phone_id}:
            if entity_id and entity_id in case.entities:
                case.entities[entity_id].add_label(label)


def _ingest_device(case: CaseGraph, row: dict[str, Any], source: str) -> None:
    imei = _pick(row, "imei", "device_imei", "device_id")
    msisdn = _pick(row, "msisdn", "phone", "number")
    ip = _pick(row, "ip", "ip_address", "src_ip")
    ts = _pick(row, "timestamp", "session_time", "date")
    app = _pick(row, "app_version", "app", "device_model")
    session = _pick(row, "session_id", "id")
    lat = _pick(row, "latitude", "lat")
    lon = _pick(row, "longitude", "lon", "lng")

    device_id = ""
    if imei:
        device_id = case.add_entity(EntityType.DEVICE, cfg.normalize_account(imei), raw=imei, source=source,
                                    attrs={"app_version": app} if app else None).id
    phone_id = ""
    if msisdn:
        phone_id = case.add_entity(EntityType.PHONE, cfg.normalize_phone(msisdn), raw=msisdn, source=source).id
    if device_id and phone_id:
        case.add_relation(device_id, phone_id, "device_used_msisdn", weight=1.5, ts=ts, source=source,
                          evidence=f"session {session or '-'}: IMEI {imei} with {msisdn}")
    if ip and device_id:
        ip_ent = case.add_entity(EntityType.IP, ip, raw=ip, source=source)
        case.add_relation(device_id, ip_ent.id, "session_ip", weight=1.0, ts=ts, source=source,
                          evidence=f"session {session or '-'} from IP {ip}")
    if lat and lon:
        loc = case.add_entity(EntityType.LOCATION, f"{lat},{lon}".upper(), raw=f"{lat},{lon}", source=source)
        if device_id:
            case.add_relation(device_id, loc.id, "located_at", weight=0.4, ts=ts, source=source,
                              evidence=f"geo {lat},{lon} at {ts or '-'}")


def _ingest_generic(case: CaseGraph, row: dict[str, Any], source: str) -> None:
    identifiers: list[str] = []
    for key, value in row.items():
        if str(key).startswith("__") or not isinstance(value, str) or not value.strip():
            continue
        spans = find_spans(value)
        if not spans:
            continue
        span = spans[0]
        entity = case.add_entity(span.etype, span.norm, raw=span.raw, source=source)
        identifiers.append(entity.id)
    for i in range(len(identifiers)):
        for j in range(i + 1, len(identifiers)):
            case.add_relation(identifiers[i], identifiers[j], "co_occur", weight=0.4,
                              source=source, evidence=str({k: v for k, v in row.items() if not str(k).startswith('__')})[:180])


def extract_all(case: CaseGraph, documents: list[Document], records: list[dict[str, Any]]) -> None:
    ingest_records(case, records)
    for doc in documents:
        if doc.kind == "structured":
            continue
        extract_from_text(case, doc)

from __future__ import annotations

import re
from typing import Any

from cfna import config as cfg
from cfna.extract.entities import apply_role_labels, nearest_entity, propagate_owner_labels
from cfna.models import CaseGraph, Document, EntityType

IDENTIFIER_ENTITIES = {
    EntityType.UPI_ID,
    EntityType.PHONE,
    EntityType.ACCOUNT,
    EntityType.DEVICE,
    EntityType.SIM,
    EntityType.CARD,
    EntityType.HANDLE,
    EntityType.EMAIL,
    EntityType.IP,
    EntityType.PAN,
}

LOSS_SUBJECT_TYPES = {
    EntityType.PERSON,
    EntityType.UPI_ID,
    EntityType.PHONE,
    EntityType.ACCOUNT,
    EntityType.CARD,
}

POSSESSION_RE = re.compile(r"\b(?:holds?|owns?|operates?|controls?|maintains?|possesses?|uses|using)\b", re.I)
POSSESSION_TARGETS = {
    EntityType.ACCOUNT,
    EntityType.UPI_ID,
    EntityType.PHONE,
    EntityType.SIM,
    EntityType.CARD,
    EntityType.DEVICE,
}

SENTENCE_SPLIT = re.compile(r"(?<=[.!?\n])\s+")
MAX_EVIDENCE = 160


def _label_line(case: CaseGraph, line: str, located: list[tuple[int, int, str]]) -> None:
    lowered = line.lower()
    apply_role_labels(case, line, located)
    if not any(marker in lowered for marker in cfg.ROLE_MARKERS["accused"]):
        return
    for _, _, entity_id in located:
        ent = case.entities.get(entity_id)
        if ent is not None:
            ent.add_label("suspect")


def _record_loss(case: CaseGraph, sentence: str, located: list[tuple[int, int, str]]) -> None:
    """`X was defrauded of Rs.N` / `Y lost Rs.N` -> store the loss on the subject entity.

    Narrative-only input has no transfer rows, so this is the only way a complaint pasted by a
    user produces a quantified victim loss for the FIR.
    """
    match = re.search(cfg.LOSS_VERBS, sentence, re.I)
    if not match:
        return
    amount = _amount_from(sentence)
    if amount <= 0:
        return
    subject = nearest_entity(located, match.end())
    if subject is None:
        return
    ent = case.entities.get(subject)
    if ent is None or ent.etype not in LOSS_SUBJECT_TYPES:
        return
    previous = float(ent.attrs.get("loss_amount") or 0.0)
    if amount > previous:
        ent.attrs["loss_amount"] = amount


def _resolve_value(case: CaseGraph, value: str) -> str | None:
    candidate = re.sub(r"\D", "", value)
    if len(candidate) >= 9:
        for etype in (EntityType.DEVICE, EntityType.SIM, EntityType.ACCOUNT, EntityType.PHONE, EntityType.CARD):
            ent = case.entities.get(f"{etype.value}:{candidate}")
            if ent is not None:
                return ent.id
    lowered = value.strip().lower()
    for etype in (EntityType.UPI_ID, EntityType.HANDLE, EntityType.EMAIL):
        ent = case.entities.get(f"{etype.value}:{lowered}")
        if ent is not None:
            return ent.id
    upper = value.strip().upper()
    ent = case.entities.get(f"{EntityType.PERSON.value}:{upper}")
    return ent.id if ent is not None else None


def _line_entities(case: CaseGraph, line: str) -> list[tuple[int, int, str]]:
    found: list[tuple[int, int, str]] = []
    for match in cfg.UPI_RE.finditer(line):
        value = match.group(1)
        if "@" in value and "." in value.split("@", 1)[1]:
            continue
        ent_id = f"{EntityType.UPI_ID.value}:{cfg.normalize_upi(value)}"
        if ent_id in case.entities:
            found.append((match.start(1), match.end(1), ent_id))
    for match in cfg.PHONE_RE.finditer(line):
        ent_id = f"{EntityType.PHONE.value}:{cfg.normalize_phone(match.group(1))}"
        if ent_id in case.entities:
            found.append((match.start(1), match.end(1), ent_id))
    for match in cfg.IMEI_RE.finditer(line):
        ent_id = f"{EntityType.DEVICE.value}:{match.group(1)}"
        if ent_id in case.entities:
            found.append((match.start(1), match.end(1), ent_id))
    for match in cfg.ICCID_RE.finditer(line):
        ent_id = f"{EntityType.SIM.value}:{match.group(1)}"
        if ent_id in case.entities:
            found.append((match.start(1), match.end(1), ent_id))
    for match in cfg.ACCOUNT_RE.finditer(line):
        ent_id = f"{EntityType.ACCOUNT.value}:{match.group(1)}"
        if ent_id in case.entities:
            found.append((match.start(1), match.end(1), ent_id))
    for match in cfg.IFSC_RE.finditer(line):
        ent_id = f"{EntityType.IFSC.value}:{cfg.normalize_ifsc(match.group(1))}"
        if ent_id in case.entities:
            found.append((match.start(1), match.end(1), ent_id))
    for match in cfg.EMAIL_RE.finditer(line):
        ent_id = f"{EntityType.EMAIL.value}:{match.group(1).lower()}"
        if ent_id in case.entities:
            found.append((match.start(1), match.end(1), ent_id))
    for match in cfg.HANDLE_RE.finditer(line):
        ent_id = f"{EntityType.HANDLE.value}:{cfg.normalize_handle(match.group(1))}"
        if ent_id in case.entities:
            found.append((match.start(1), match.end(1), ent_id))
    for match in cfg.NAME_AFTER_RE.finditer(line):
        ent_id = f"{EntityType.PERSON.value}:{match.group(1).strip().upper()}"
        if ent_id in case.entities:
            found.append((match.start(1), match.end(1), ent_id))
    found.sort()
    deduped: list[tuple[int, int, str]] = []
    last_end = -1
    for start, end, ent_id in found:
        if start >= last_end:
            deduped.append((start, end, ent_id))
            last_end = end
    return deduped


def _amount_from(line: str) -> float:
    for match in cfg.MONEY_RE.finditer(line):
        value = cfg.money_to_float(match.group(1))
        if value:
            return value
    for match in cfg.MONEY_WORD_RE.finditer(line):
        value = cfg.money_to_float(match.group(1))
        if value:
            return cfg.scale_money(value, match.group(2))
    return 0.0


def extract_text_relations(case: CaseGraph, documents: list[Document]) -> None:
    for doc in documents:
        if doc.kind == "structured":
            continue
        for line in doc.lines:
            if len(line) < 12:
                continue
            for sentence in SENTENCE_SPLIT.split(line):
                _process_sentence(case, doc, sentence)
    propagate_owner_labels(case)


def _process_sentence(case: CaseGraph, doc: Document, sentence: str) -> None:
    located = _line_entities(case, sentence)
    if not located:
        return
    entity_ids = [ent_id for _, _, ent_id in located]
    _label_line(case, sentence, located)
    _record_loss(case, sentence, located)

    added = _explicit_links(case, doc, sentence, located)
    added += _transfer_links(case, doc, sentence, located)
    added += _possession_links(case, doc, sentence, located)
    if not added and len(entity_ids) >= 2:
        pairs = [(entity_ids[i], entity_ids[j]) for i in range(len(entity_ids)) for j in range(i + 1, len(entity_ids))]
        for src, dst in pairs[:6]:
            case.add_relation(
                src, dst, "co_occur", weight=0.35, source=doc.path,
                evidence=sentence.strip()[:MAX_EVIDENCE],
            )


def _explicit_links(case: CaseGraph, doc: Document, sentence: str, located: list[tuple[int, int, str]]) -> int:
    added = 0
    for pattern, rtype, weight in cfg.TEXT_LINK_PATTERNS:
        for match in pattern.finditer(sentence):
            captured = [g for g in match.groups() if g]
            resolved: list[str] = []
            for group in captured:
                ent_id = _resolve_value(case, group)
                if ent_id:
                    resolved.append(ent_id)
            if len(resolved) < 2:
                inner = [ent_id for start, end, ent_id in located if start >= match.start() and end <= match.end()]
                resolved = inner
            for i in range(len(resolved) - 1):
                case.add_relation(
                    resolved[i], resolved[i + 1], rtype, weight=weight, source=doc.path,
                    evidence=sentence.strip()[:MAX_EVIDENCE],
                )
                added += 1
    return added


def _transfer_links(case: CaseGraph, doc: Document, sentence: str, located: list[tuple[int, int, str]]) -> int:
    if not re.search(cfg.TRANSFER_VERBS, sentence, re.I):
        return 0
    amount = _amount_from(sentence)
    identifiers = [(start, end, ent_id) for start, end, ent_id in located
                   if case.entities[ent_id].etype in IDENTIFIER_ENTITIES]
    if len(identifiers) < 2 or amount <= 0:
        return 0
    added = 0
    src, dst = identifiers[0][2], identifiers[1][2]
    case.add_relation(
        src, dst, "transfer", weight=1.0, amount=amount, source=doc.path,
        evidence=sentence.strip()[:MAX_EVIDENCE],
    )
    return added + 1


def _possession_links(case: CaseGraph, doc: Document, sentence: str, located: list[tuple[int, int, str]]) -> int:
    """"Anup Saha holds account 5001000000001" -> person owns account.

    Narrative input has no KYC/ownership rows, so possession verbs are the only signal that the
    person in the sentence controls the identifier next to them (which is also how role labels
    travel down to the money-holding account).
    """
    if not POSSESSION_RE.search(sentence):
        return 0
    people = [ent_id for _, _, ent_id in located if case.entities[ent_id].etype == EntityType.PERSON]
    targets = [ent_id for _, _, ent_id in located if case.entities[ent_id].etype in POSSESSION_TARGETS]
    if len(people) != 1 or not targets:
        return 0
    evidence = sentence.strip()[:MAX_EVIDENCE]
    for target in targets:
        case.add_relation(people[0], target, "owns", weight=1.3, source=doc.path, evidence=evidence)
    return len(targets)


def compute_document_index(case: CaseGraph) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for doc in case.documents:
        if doc.kind == "structured":
            continue
        index[doc.path] = doc.lines
    return index

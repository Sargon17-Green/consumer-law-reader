"""Strict, code-free reader for FOI canonical-legislative-sources v1 snapshots.

This module does NOT execute P***/R*** Python models. Such models require a
separate, explicit, trusted export process. Structural success is not a legal
source-fidelity certification and does not authorize publication.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from urllib.parse import urlsplit
from typing import Any

FORMAT = "canonical-legislative-sources"
FORMAT_VERSION = 1
SOURCE_SCHEMA_SHA256 = "3bc9cd62e1a34978192b9eca3b4daa3eb5db9a5a3ee070e32b821e439f4373f3"

# Static, exact field contracts transcribed from the pinned v160/v261
# canonical_source_schema.py (not imported/executed by the reader).
# s: string; ? optional (null); i: integer, b: boolean; n: int|string;
# [T]: list of T; *: content node or JSON scalar; @T: exact typed object.
SCHEMA: dict[str, dict[str, str]] = {
    "Heading": {"id":"s", "text":"s"},
    "Paragraph": {"id":"s", "text":"s"},
    "Unreadable": {"id":"s", "text":"s"},
    "Irrelevant": {"id":"s", "text":"s", "comment":"s?"},
    "PageMarker": {"id":"s", "source_page":"i?", "printed_page":"n?"},
    "PublicationNote": {"id":"s", "content":"[*]"},
    "Footnote": {"id":"s", "marker":"s", "content":"[*]"},
    "FootnoteRef": {"id":"s", "marker":"s", "footnote_id":"s"},
    "Definition": {"id":"s", "term":"s", "content":"[*]"},
    "NumberedItem": {"id":"s", "number":"s", "content":"[*]"},
    "Subsection": {"id":"s", "number":"s", "content":"[*]"},
    "LegalProvision": {"id":"s", "number":"s", "side_title":"s?", "content":"[*]"},
    "LegalSchedule": {"id":"s", "title":"s", "provision_ref":"s?", "citation":"s?", "content":"[*]"},
    "TableCell": {"id":"s", "content":"[*]", "span":"i"},
    "TableRow": {"id":"s", "cells":"[@TableCell]"},
    "Table": {"id":"s", "rows":"[@TableRow]"},
    "ExplanatoryParagraph": {"id":"s", "content":"[*]", "provision_ref":"s?"},
    "ExplanatoryNotes": {"id":"s", "content":"[*]"},
    "ReservationSection": {"id":"s", "target_text":"s", "content":"[*]"},
    "Reservation": {"id":"s", "proposers":"[s]", "content":"[*]", "alternative_to":"s?"},
    "Continuation": {"id":"s", "target_id":"s", "content":"[*]"},
    "ProceduralNote": {"id":"s", "content":"[*]"},
    "QuotedText": {"id":"s", "content":"[*]"},
    "Vote": {"id":"s", "subject":"s?", "vote_number":"s?", "for_count":"i?", "against_count":"i?", "abstain_count":"i?", "result":"s?", "raw_text":"s"},
    "Decision": {"id":"s", "content":"[*]"},
    "Announcement": {"id":"s", "content":"[*]"},
    "Interjection": {"id":"s", "speaker":"s?", "content":"[*]"},
    "SpeakerTurn": {"id":"s", "speaker":"s", "role":"s?", "content":"[*]"},
    "Participant": {"id":"s", "name":"s", "role":"s?"},
    "ParticipantGroup": {"id":"s", "title":"s", "participants":"[@Participant]"},
    "AgendaItem": {"id":"s", "title":"s", "content":"[*]"},
    "PlenaryAgendaItem": {"id":"s", "title":"s", "content":"[*]"},
    "BillMetadata": {"knesset":"s?", "proposal_number":"s?", "publication_series":"s?", "publication_number":"s?", "publication_date":"s?", "publication_page":"s?", "sponsors":"[s]"},
    "BillPart": {"id":"s", "title":"s?", "proposal_number":"s?", "sponsors":"[s]", "content":"[*]"},
    "BillDocument": {"source_url":"s", "source_filename":"s", "title":"s", "metadata":"@BillMetadata", "content":"[*]"},
    "CommitteeProtocolMetadata": {"knesset":"s?", "session":"s?", "committee":"s?", "protocol_number":"s?", "date":"s?", "start_time":"s?", "status_note":"s?"},
    "CommitteeProtocol": {"source_url":"s", "source_filename":"s", "metadata":"@CommitteeProtocolMetadata", "participants":"[@ParticipantGroup]", "agenda":"[*]", "closing":"[*]"},
    "PlenaryProtocolMetadata": {"knesset":"s?", "sitting_number":"s?", "date":"s?", "start_time":"s?", "chair":"[s]"},
    "PlenaryProtocol": {"source_url":"s", "source_filename":"s", "metadata":"@PlenaryProtocolMetadata", "table_of_contents":"[*]", "agenda":"[*]", "closing":"[*]"},
    "LegislativeSource": {"document":"*", "phase":"s?", "date":"s?", "location":"s?", "law_name":"s", "relevant_parts":"[s]"},
    "MissingSource": {"date":"s?", "description":"s", "source_url":"s?", "note":"s"},
}

ROOTS = {"bill": "BillDocument", "committee_protocol": "CommitteeProtocol", "plenary_protocol": "PlenaryProtocol"}
REFERENCE_FIELDS = {"FootnoteRef": {"footnote_id": "Footnote"}, "Continuation": {"target_id": None},
    "Reservation": {"alternative_to": None}, "LegalSchedule": {"provision_ref": "LegalProvision"},
    "ExplanatoryParagraph": {"provision_ref": "LegalProvision"}}


class CanonicalSnapshotError(ValueError):
    """A structural, typing, identity, or reference violation."""


def _fail(where: str, why: str) -> None:
    raise CanonicalSnapshotError(f"{where}: {why}")


def _pairs_unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, val in pairs:
        if name in result:
            _fail("JSON", f"duplicate property {name!r}")
        result[name] = val
    return result


def _reject_constant(value: str) -> Any:
    _fail("JSON", f"non-finite numeric constant {value}")


def _exact_keys(obj: Any, names: set[str], where: str) -> None:
    if not isinstance(obj, dict):
        _fail(where, "expected JSON object")
    missing, extra = names - obj.keys(), obj.keys() - names
    if missing or extra:
        _fail(where, f"missing={sorted(missing)!r}; unexpected={sorted(extra)!r}")


def _text(value: Any, where: str, *, nonempty: bool = False) -> str:
    if type(value) is not str or (nonempty and not value.strip()):
        _fail(where, "expected nonempty string" if nonempty else "expected string")
    return value


def _source_url(value: str, where: str) -> None:
    try:
        u = urlsplit(value)
        hostname = u.hostname
    except ValueError:
        _fail(where, "malformed source URL")
    if u.scheme not in {"https", "http"} or not hostname or u.username or u.password:
        _fail(where, "invalid or unsafe source URL")
    try:
        _ = u.port
    except ValueError:
        _fail(where, "invalid URL port")


def _validate_tree(node: Any, where: str, ids: dict[str, str], refs: list[tuple[str, str, str | None]], depth: int = 0, *, expected: str | None = None) -> None:
    if depth > 160:
        _fail(where, "maximum canonical nesting depth exceeded")
    if not isinstance(node, dict):
        _fail(where, "expected typed node")
    _exact_keys(node, {"$type", "fields"}, where)
    name = _text(node["$type"], f"{where}.$type", nonempty=True)
    if name not in SCHEMA or (expected is not None and name != expected):
        _fail(where, f"unexpected or unknown canonical type {name!r}")
    f = node["fields"]
    _exact_keys(f, set(SCHEMA[name]), f"{where}.fields")
    node_id = f.get("id")
    if node_id is not None:
        _text(node_id, f"{where}.fields.id", nonempty=True)
        if node_id in ids:
            _fail(where, f"duplicate canonical node id {node_id!r}")
        ids[node_id] = name
        if len(ids) > 250_000:
            _fail(where, "node count limit exceeded")
    for field, typ in SCHEMA[name].items():
        p, v = f"{where}.{field}", f[field]
        _validate_type(v, typ, p, ids, refs, depth + 1)
    if name in REFERENCE_FIELDS:
        for field, target_type in REFERENCE_FIELDS[name].items():
            value = f[field]
            if value is not None:
                refs.append((f"{where}.{field}", value, target_type))
    if name in ROOTS.values():
        _source_url(f["source_url"], f"{where}.source_url")


def _validate_type(v: Any, typ: str, p: str, ids: dict[str, str], refs: list[tuple[str, str, str | None]], depth: int) -> None:
    if depth > 160:
        _fail(p, "maximum canonical nesting depth exceeded")
    if typ.endswith("?"):
        if v is None:
            return
        typ = typ[:-1]
    if typ.startswith("["):
        if not isinstance(v, list):
            _fail(p, "expected array")
        for i, child in enumerate(v):
            _validate_type(child, typ[1:-1], f"{p}[{i}]", ids, refs, depth + 1)
    elif typ.startswith("@"):
        _validate_tree(v, p, ids, refs, depth + 1, expected=typ[1:])
    elif typ == "*":
        if isinstance(v, dict):
            _validate_tree(v, p, ids, refs, depth + 1)
        elif isinstance(v, list):
            for i, child in enumerate(v):
                _validate_type(child, "*", f"{p}[{i}]", ids, refs, depth + 1)
        elif v is not None and (type(v) not in (str, int, float, bool) or (type(v) is float and not math.isfinite(v))):
            _fail(p, "invalid canonical content value")
    elif typ == "s":
        _text(v, p)
    elif typ == "i":
        if type(v) is not int:
            _fail(p, "expected integer (not boolean)")
    elif typ == "n":
        if type(v) not in (str, int):
            _fail(p, "expected source page string or integer")
    else:
        _fail(p, f"internal schema error for {typ!r}")


def validate_snapshot(data: Any) -> dict[str, Any]:
    """Check the entire v1 snapshot without running any source Python.

    Returns the input object unchanged, never a rendered or legally approved item.
    """
    _exact_keys(data, {"format", "format_version", "source_schema_sha256", "source_archive_sha256", "entries"}, "snapshot")
    if data["format"] != FORMAT or type(data["format_version"]) is not int or data["format_version"] != FORMAT_VERSION:
        _fail("snapshot", "unsupported canonical snapshot format/version")
    if data["source_schema_sha256"] != SOURCE_SCHEMA_SHA256:
        _fail("snapshot.source_schema_sha256", "unknown canonical source schema")
    archive_sha = data["source_archive_sha256"]
    if archive_sha is not None and (type(archive_sha) is not str or len(archive_sha) != 64 or any(c not in "0123456789abcdef" for c in archive_sha)):
        _fail("snapshot.source_archive_sha256", "expected lowercase SHA-256 or null")
    entries = data["entries"]
    if not isinstance(entries, list):
        _fail("snapshot.entries", "expected array")
    seen_source, seen_document = set(), set()
    for index, entry in enumerate(entries):
        path = f"entries[{index}]"
        _exact_keys(entry, {"source_id", "document_id", "kind", "document", "associations", "provenance", "verification"}, path)
        source_id = _text(entry["source_id"], f"{path}.source_id", nonempty=True)
        document_id = _text(entry["document_id"], f"{path}.document_id", nonempty=True)
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", source_id):
            _fail(f"{path}.source_id", "unsafe source identifier")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", document_id):
            _fail(f"{path}.document_id", "unsafe document identifier")
        if source_id in seen_source or document_id in seen_document:
            _fail(path, "duplicate source_id or document_id")
        seen_source.add(source_id)
        seen_document.add(document_id)
        kind = entry["kind"]
        if type(kind) is not str or kind not in ROOTS:
            _fail(f"{path}.kind", "unsupported source kind")
        ids: dict[str, str] = {}
        refs: list[tuple[str, str, str | None]] = []
        _validate_tree(entry["document"], f"{path}.document", ids, refs, expected=ROOTS[kind])
        assocs = entry["associations"]
        if not isinstance(assocs, list):
            _fail(f"{path}.associations", "expected array")
        for j, assoc in enumerate(assocs):
            ap = f"{path}.associations[{j}]"
            _exact_keys(assoc, {"document_id", "phase", "date", "location", "law_name", "relevant_parts"}, ap)
            if assoc["document_id"] != document_id:
                _fail(ap, "association document_id must match its entry")
            for k in ("phase", "date", "location"):
                if assoc[k] is not None:
                    _text(assoc[k], f"{ap}.{k}")
            _text(assoc["law_name"], f"{ap}.law_name", nonempty=True)
            if not isinstance(assoc["relevant_parts"], list):
                _fail(ap, "relevant_parts must be an array")
            for j2, ref in enumerate(assoc["relevant_parts"]):
                _text(ref, f"{ap}.relevant_parts[{j2}]", nonempty=True)
                refs.append((f"{ap}.relevant_parts[{j2}]", ref, None))
        # Verification metadata is preserved but never trusted as publication authorization.
        for k in ("provenance", "verification"):
            if entry[k] is not None and not isinstance(entry[k], dict):
                _fail(f"{path}.{k}", "expected JSON metadata object or null")
        for ref_path, ref, required_type in refs:
            if ref not in ids:
                _fail(ref_path, f"unresolved canonical node id {ref!r}")
            if required_type and ids[ref] != required_type:
                _fail(ref_path, f"target must be {required_type}, not {ids[ref]}")
    return data


def load_snapshot(path: str | Path) -> dict[str, Any]:
    """Load strict JSON (duplicate-key rejection) and verify its entire graph."""
    with Path(path).open("r", encoding="utf-8") as stream:
        value = json.load(stream, object_pairs_hook=_pairs_unique, parse_constant=_reject_constant)
    return validate_snapshot(value)

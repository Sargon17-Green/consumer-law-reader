"""Build a deterministic, source-first search index from *validated* canonical JSON.

No archive Python is imported; no network requests, HTML generation, or
legal-fidelity certification occur here. The source document URL is preserved
byte-for-byte and an official *page* URL is never inferred.
"""
from __future__ import annotations

from copy import deepcopy
from urllib.parse import urlsplit
from typing import Any
import base64

from .canonical_snapshot import validate_snapshot

INDEX_FORMAT = "legal-legislative-source-search-index"
INDEX_VERSION = 1

# Only fields that contain display/search text, never identifiers, URLs or
# machine metadata. Every typed child is traversed, even in unknown containers.
TEXT_FIELDS: dict[str, tuple[str, ...]] = {
    "Heading": ("text",),
    "Paragraph": ("text",),
    "Unreadable": ("text",),
    "Irrelevant": ("text",),
    "Definition": ("term",),
    "LegalProvision": ("side_title",),
    "LegalSchedule": ("title",),
    "ReservationSection": ("target_text",),
    "AgendaItem": ("title",),
    "PlenaryAgendaItem": ("title",),
    "BillPart": ("title",),
    "Participant": ("name",),
    "SpeakerTurn": ("speaker",),
    "Interjection": ("speaker",),
    "Vote": ("raw_text",),
}


def _anchor(source_id: str, node_id: str) -> str:
    # IDs in FOI are arbitrary Unicode; use reversible, HTML-safe UTF-8 base64.
    encoded = base64.urlsafe_b64encode(node_id.encode("utf-8")).decode("ascii").rstrip("=")
    return f"src-{source_id}--{encoded}"


def _link_status(url: str) -> tuple[str, bool]:
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower().rstrip(".")
    knesset = host == "knesset.gov.il" or host.endswith(".knesset.gov.il")
    if knesset and parsed.scheme == "https":
        return "KNESSET_HOST_SYNTAX_ONLY", True
    if knesset:
        return "INSECURE_HTTP_KNESSET_HOST", False
    return "EXTERNAL_HOST_UNVERIFIED", False


def _metadata(root: dict[str, Any]) -> dict[str, Any]:
    node = root["fields"].get("metadata")
    return deepcopy(node["fields"]) if isinstance(node, dict) else {}


def _title(root: dict[str, Any], meta: dict[str, Any]) -> str | None:
    return root["fields"].get("title") or meta.get("committee") or None


def build_search_index(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Validate and index canonical JSON without modifying the input.

    Indexing does not establish that text matches a scanned/Word original.
    A KNESSET_HOST_SYNTAX_ONLY link is not a live-link verification.
    """
    validate_snapshot(snapshot)
    sources: list[dict[str, Any]] = []
    segments: list[dict[str, Any]] = []
    associations: list[dict[str, Any]] = []
    votes: list[dict[str, Any]] = []
    for entry in snapshot["entries"]:
        source_id, document_id = entry["source_id"], entry["document_id"]
        root = entry["document"]
        fields = root["fields"]
        url = fields["source_url"]
        status, primary_allowed = _link_status(url)
        meta = _metadata(root)
        sources.append({
            "source_id": source_id,
            "document_id": document_id,
            "kind": entry["kind"],
            "title": _title(root, meta),
            "metadata": meta,
            "original_document_url": url,
            "source_filename": fields["source_filename"],
            "official_page_url": None,
            "link_validation": status,
            "primary_link_allowed": primary_allowed,
            "normalized_date": None,
        })
        for assoc in entry["associations"]:
            associations.append({"source_id": source_id, **deepcopy(assoc)})
        state: dict[str, Any] = {"speaker": None, "agenda_id": None,
                                 "source_page": None, "printed_page": None}
        # Track text already present in an immediate sibling Paragraph, so a
        # Vote.raw_text does not index that exact source passage a second time.
        def visit(value: Any, state: dict[str, Any], path: str = "root",
                  owner: dict[str, Any] | None = None, scalar_text: bool = False,
                  suppress_vote_text: bool = False) -> None:
            if isinstance(value, str):
                if scalar_text and value:
                    node_id = owner.get("id") if owner else None
                    segments.append({
                        "source_id": source_id, "document_id": document_id,
                        "node_id": node_id, "node_type": owner.get("type") if owner else root["$type"],
                        "field": "content_text", "order": len(segments), "text": value,
                        "anchor": _anchor(source_id, node_id or path),
                        "source_path": path, "text_role": "source_text",
                        "speaker": state["speaker"], "agenda_id": state["agenda_id"],
                        "source_page": state["source_page"], "printed_page": state["printed_page"],
                    })
                return
            if isinstance(value, list):
                sibling_paragraphs = {
                    x["fields"]["text"] for x in value
                    if isinstance(x, dict) and x.get("$type") == "Paragraph"
                }
                for i, child in enumerate(value):
                    # Suppress duplicated vote *text*, never its semantic event.
                    duplicate_vote = (isinstance(child, dict)
                        and child.get("$type") == "Vote"
                        and child["fields"]["raw_text"] in sibling_paragraphs)
                    visit(child, state, f"{path}[{i}]", owner, scalar_text,
                          suppress_vote_text=duplicate_vote)
                return
            if not isinstance(value, dict) or "$type" not in value:
                return
            typ, node = value["$type"], value["fields"]
            if typ == "PageMarker":
                state["source_page"] = node["source_page"]
                state["printed_page"] = node["printed_page"]
                return
            local = state.copy()
            if typ == "SpeakerTurn":
                local["speaker"] = node["speaker"]
            elif typ in ("AgendaItem", "PlenaryAgendaItem"):
                local["agenda_id"] = node["id"]
            node_id = node.get("id")
            if typ == "Vote":
                votes.append({
                    "source_id": source_id, "document_id": document_id,
                    "node_id": node_id, "anchor": _anchor(source_id, node_id),
                    "source_path": path, "speaker": local["speaker"],
                    "agenda_id": local["agenda_id"],
                    "source_page": local["source_page"],
                    "printed_page": local["printed_page"],
                    "subject": node["subject"], "vote_number": node["vote_number"],
                    "for_count": node["for_count"],
                    "against_count": node["against_count"],
                    "abstain_count": node["abstain_count"],
                    "result": node["result"],
                    "raw_text": node["raw_text"],
                    "raw_text_indexed": not suppress_vote_text,
                })
            if node_id is not None:
                for field in TEXT_FIELDS.get(typ, ()):
                    value_text = node[field]
                    if not isinstance(value_text, str) or not value_text:
                        continue
                    if typ == "Vote" and field == "raw_text" and suppress_vote_text:
                        continue
                    role = ("excluded_marker" if typ == "Irrelevant" else
                            "unreadable_marker" if typ == "Unreadable" else
                            "vote_raw" if typ == "Vote" else
                            "context_label" if field in ("speaker", "name") else
                            "source_text")
                    segments.append({
                        "source_id": source_id, "document_id": document_id,
                        "node_id": node_id, "node_type": typ, "field": field,
                        "order": len(segments), "text": value_text,
                        "anchor": _anchor(source_id, node_id),
                        "source_path": f"{path}.{field}", "text_role": role,
                        "speaker": local["speaker"], "agenda_id": local["agenda_id"],
                        "source_page": local["source_page"],
                        "printed_page": local["printed_page"],
                    })
            for field, child in node.items():
                # Do not index arbitrary machine metadata as text; recurse only
                # into typed children and arrays containing typed children.
                if field in ("metadata",):
                    continue
                if isinstance(child, (list, dict)):
                    visit(child, local, f"{path}.{field}",
                          {"id": node_id, "type": typ},
                          scalar_text=(field in {"content", "agenda", "closing", "table_of_contents"}))
            # Page markers inside a container must propagate in source order.
            for field in ("source_page", "printed_page"):
                state[field] = local[field]

        visit(root, state)
    return {
        "format": INDEX_FORMAT,
        "format_version": INDEX_VERSION,
        "source_schema_sha256": snapshot["source_schema_sha256"],
        "source_archive_sha256": snapshot["source_archive_sha256"],
        "sources": sources,
        "segments": segments,
        "associations": associations,
        "votes": votes,
        "publication_authorized": False,
    }


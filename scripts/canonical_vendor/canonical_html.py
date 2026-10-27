"""Non-publishing, lossless-by-fields HTML preview of validated FOI typed sources.

This is an inspection preview, NOT a legally certified rendering or a substitute
for the 3.7.0 HTML/DOCX/PDF layout. No source Python, HTML markup, scripts,
remote resources or external CSS are executed or imported.
"""
from __future__ import annotations

from html import escape
import json
from typing import Any

from .canonical_snapshot import validate_snapshot
from .canonical_search import _anchor, _link_status


class _Renderer:
    def __init__(self, source_id: str):
        self.source_id = source_id

    @staticmethod
    def _e(value: Any) -> str:
        return escape(str(value), quote=True)

    def _scalar(self, value: Any) -> str:
        if value is None:
            return '<span class="canonical-null" data-value-kind="null">null</span>'
        if type(value) is bool:
            return f'<span data-value-kind="bool">{str(value).lower()}</span>'
        if type(value) is int:
            return f'<span data-value-kind="int">{value}</span>'
        if type(value) is float:
            return f'<span data-value-kind="float">{self._e(value)}</span>'
        return f'<span data-value-kind="string">{self._e(value)}</span>'

    def _value(self, value: Any) -> str:
        if isinstance(value, dict) and "$type" in value:
            return self.node(value)
        if isinstance(value, list):
            return '<ol class="canonical-sequence">' + ''.join(
                '<li>' + self._value(item) + '</li>' for item in value
            ) + '</ol>'
        # No untyped dicts are accepted by the pinned typed-node schema.
        if isinstance(value, dict):
            raise ValueError('untyped dictionary in canonical content')
        return self._scalar(value)

    def _table(self, node: dict[str, Any]) -> str:
        rows = node["fields"]["rows"]
        body = []
        for row in rows:
            cells = []
            for cell in row["fields"]["cells"]:
                fields = cell["fields"]
                span = fields["span"]
                # Preserve nonpositive/invalid colspan as source data, rather
                # than silently inventing a valid span.
                colspan = f' colspan="{span}"' if type(span) is int and span > 0 else ''
                cells.append(f'<td id="{self._e(_anchor(self.source_id, fields["id"]))}"'
                             f' data-type="TableCell" data-node-id="{self._e(fields["id"])}"'
                             f' data-source-span="{self._e(span)}"{colspan}>'
                             + self._value(fields["content"]) + '</td>')
            body.append(f'<tr id="{self._e(_anchor(self.source_id, row["fields"]["id"]))}"'
                        f' data-type="TableRow" data-node-id="{self._e(row["fields"]["id"])}">'
                        + ''.join(cells) + '</tr>')
        return '<table class="canonical-table"><tbody>' + ''.join(body) + '</tbody></table>'

    def node(self, node: dict[str, Any]) -> str:
        typ, fields = node["$type"], node["fields"]
        node_id = fields.get("id")
        anchor = (f' id="{self._e(_anchor(self.source_id, node_id))}"'
                  if node_id is not None else '')
        node_attr = (f' data-node-id="{self._e(node_id)}"' if node_id is not None else '')
        content = []
        for name, value in fields.items():
            if name == "id":
                continue  # retained as data-node-id, not repeated as source text
            if typ == "Table" and name == "rows":
                content.append(self._table(node))
                continue
            if typ == "FootnoteRef" and name == "footnote_id":
                target = _anchor(self.source_id, value)
                rendered = (f'<a href="#{self._e(target)}">{self._e(value)}</a>')
            else:
                rendered = self._value(value)
            content.append(f'<div class="canonical-field" data-field="{self._e(name)}">'
                           f'<span class="canonical-field-label">{self._e(name)}</span>'
                           f'{rendered}</div>')
        css_class = ' canonical-marker' if typ in ('Irrelevant', 'Unreadable') else ''
        return (f'<section class="canonical-node{css_class}" data-type="{self._e(typ)}"'
                f'{node_attr}{anchor}><h3>{self._e(typ)}</h3>'
                + ''.join(content) + '</section>')


def render_snapshot_html(snapshot: dict[str, Any]) -> str:
    """Produce a deterministic, offline HTML inspection view, never a legal publication.

    Every source field remains visible as escaped literal text or a typed child.
    Source URLs are linked only for HTTPS Knesset-host syntax, without any claim
    that the URL is live or authoritative. No official page URL is inferred.
    """
    validate_snapshot(snapshot)
    articles = []
    for entry in snapshot["entries"]:
        sid = entry["source_id"]
        root = entry["document"]
        renderer = _Renderer(sid)
        original_url = root["fields"]["source_url"]
        link_status, link_allowed = _link_status(original_url)
        source_display = escape(original_url, quote=True)
        source_label = (f'<a href="{source_display}" rel="noopener noreferrer">'
                        f'{source_display}</a>' if link_allowed else
                        f'<span>{source_display}</span>')
        assocs = []
        for association in entry["associations"]:
            assoc_fields = []
            for key, value in association.items():
                if key == "relevant_parts":
                    # References are guaranteed to resolve by validate_snapshot.
                    rendered = '<ol class="canonical-sequence">' + ''.join(
                        f'<li><a href="#{escape(_anchor(sid, ref), quote=True)}">'
                        f'{escape(ref, quote=True)}</a></li>' for ref in value
                    ) + '</ol>'
                else:
                    rendered = renderer._value(value)
                assoc_fields.append(
                    f'<div class="canonical-field" data-field="{escape(key, quote=True)}">'
                    f'<span class="canonical-field-label">{escape(key, quote=True)}</span>'
                    f'{rendered}</div>'
                )
            assocs.append('<section class="canonical-association"><h3>association</h3>'
                          + ''.join(assoc_fields) + '</section>')
        audit_fields = []
        for field in ("provenance", "verification"):
            # Metadata is evidence about the source, not a publication gate.
            # Keep its exact JSON structure as escaped text, not executable HTML.
            encoded = json.dumps(entry[field], ensure_ascii=False, sort_keys=True,
                                 separators=(",", ":"), allow_nan=False)
            audit_fields.append(
                f'<details data-entry-field="{field}"><summary>{field}</summary>'
                f'<pre>{escape(encoded, quote=True)}</pre></details>'
            )
        articles.append(
            f'<article data-source-id="{escape(sid, quote=True)}"'
            f' data-document-id="{escape(entry["document_id"], quote=True)}"'
            f' data-kind="{escape(entry["kind"], quote=True)}">'
            f'<h2>{escape(sid)} — {escape(entry["kind"])}</h2>'
            '<aside class="source-metadata"><strong>Original source URL:</strong> '
            f'{source_label}<span class="link-status"> [{escape(link_status)}]</span></aside>'
            + renderer.node(root)
            + '<aside class="canonical-associations"><h2>Legislative associations</h2>'
            + ''.join(assocs) + '</aside>' + ''.join(audit_fields) + '</article>'
        )
    return ('<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Canonical legislative sources — unverified inspection preview</title>'
            '<style>body{font:1rem/1.5 sans-serif;max-width:80rem;margin:auto;padding:1rem}'
            '.canonical-node{border-inline-start:2px solid #aaa;padding-inline-start:1rem;margin:1rem 0}'
            '.canonical-field{margin:.4rem 0;white-space:pre-wrap;overflow-wrap:anywhere}'
            '.canonical-field-label{font-family:monospace;margin-inline-end:.8rem}'
            '.canonical-sequence{padding-inline-start:2rem}.canonical-sequence>li{margin:.4rem 0}'
            '.canonical-table{border-collapse:collapse}.canonical-table td{border:1px solid #888;padding:.5rem}'
            '.canonical-marker{border:2px dashed #555}.canonical-null{font-style:italic}'
            'a{overflow-wrap:anywhere}</style></head><body>'
            '<header><h1>Canonical legislative sources — inspection preview</h1>'
            '<p>UNVERIFIED. NOT FOR LEGAL PUBLICATION. Source text is escaped literally; '
            'this preview is not an official legal document or a fidelity certification.</p></header>'
            + ''.join(articles) + '</body></html>')


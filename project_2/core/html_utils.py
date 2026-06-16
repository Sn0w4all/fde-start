"""Deterministic HTML-document extraction and validation.

The model sometimes wraps its answer in markdown fences or prepends commentary
("Looking at the problem zones, I need to fix...") before the document. Slicing
the standalone document out is free and reliable — far cheaper and safer than
asking the model to regenerate just to drop a preamble.
"""
from __future__ import annotations

import re

_FENCE_RE = re.compile(r"^\s*```(?:html)?\s*|\s*```\s*$", re.IGNORECASE)
_DOCTYPE_RE = re.compile(r"<!doctype\s+html", re.IGNORECASE)
_HTML_OPEN_RE = re.compile(r"<html[\s>]", re.IGNORECASE)
_HTML_CLOSE = "</html>"


def extract_html_document(text: str) -> str:
    """Return just the HTML document, dropping any prose/fences around it.

    Strips markdown fences, then slices from the first ``<!DOCTYPE html>`` /
    ``<html ...>`` to the last ``</html>``. If no document markers are present
    the (fence-stripped) text is returned unchanged so validation can reject it.
    """
    t = (text or "").strip()
    if t.startswith("```"):
        t = _FENCE_RE.sub("", t).strip()

    start_match = _DOCTYPE_RE.search(t) or _HTML_OPEN_RE.search(t)
    if not start_match:
        return t  # no recognizable document — let the validator reject it
    start = start_match.start()

    close_idx = t.lower().rfind(_HTML_CLOSE)
    if close_idx == -1:
        return t[start:].strip()
    return t[start : close_idx + len(_HTML_CLOSE)].strip()


def looks_like_html_document(html: str) -> bool:
    """True iff ``html`` is a clean standalone document with no stray prose.

    Used as the artifact guard: a doc with leading commentary fails the
    ``startswith`` check, so the validator can flag it.
    """
    t = (html or "").strip().lower()
    if not t:
        return False
    if not (t.startswith("<!doctype html") or t.startswith("<html")):
        return False
    return _HTML_CLOSE in t

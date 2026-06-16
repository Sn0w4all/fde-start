"""Deterministic artifact-stripping / document-validation tests (no network)."""
from core.html_utils import extract_html_document, looks_like_html_document

# The exact preamble that leaked into a real generated file.
_PREAMBLE = (
    "Looking at the problem zones (r1c3, r2c3, r3c3 - the phone/right column), "
    "I need to fix:\n1. The phone should be narrower\n2. dark styling\n\n"
)
_DOC = "<!DOCTYPE html>\n<html lang=\"ru\"><head></head><body><h1>x</h1></body></html>"


def test_strips_leading_commentary_before_doctype():
    out = extract_html_document(_PREAMBLE + _DOC)
    assert out == _DOC
    assert out.lower().startswith("<!doctype html")
    assert "Looking at the problem zones" not in out


def test_strips_trailing_prose_after_close():
    out = extract_html_document(_DOC + "\n\nHope this helps! Let me know.")
    assert out == _DOC
    assert "Hope this helps" not in out


def test_strips_markdown_fences():
    out = extract_html_document("```html\n" + _DOC + "\n```")
    assert out == _DOC


def test_clean_doc_unchanged():
    assert extract_html_document(_DOC) == _DOC


def test_handles_html_without_doctype_and_case():
    raw = "preamble <HTML><body>hi</body></HTML> trailing"
    out = extract_html_document(raw)
    assert out == "<HTML><body>hi</body></HTML>"


def test_no_document_returns_text_for_validator():
    out = extract_html_document("just some prose, no markup at all")
    assert out == "just some prose, no markup at all"


def test_looks_like_document_accepts_clean():
    assert looks_like_html_document(_DOC) is True
    assert looks_like_html_document("<html><body>x</body></html>") is True


def test_looks_like_document_rejects_preamble_and_junk():
    assert looks_like_html_document(_PREAMBLE + _DOC) is False  # leading prose
    assert looks_like_html_document("just prose") is False
    assert looks_like_html_document("") is False
    assert looks_like_html_document("<!DOCTYPE html><html>") is False  # no close

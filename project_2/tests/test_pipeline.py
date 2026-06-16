"""Pipeline logic tests with mocked LLM + a fake renderer (no network/Chromium)."""
import pytest

from core import pipeline
from core.compare import CompareResult
from core.render import RenderError, RenderResult

CLEAN = "<!DOCTYPE html><html><body>ok</body></html>"
CLEAN2 = "<!DOCTYPE html><html><body>v2</body></html>"
DIRTY = "Looking at the problem zones, I need to fix... (not a document)"


class FakeRenderer:
    """Renders anything to a tiny PNG with no console errors."""

    def __init__(self, console_errors=None):
        self.console_errors = console_errors or []
        self.calls = 0

    async def render(self, html, **kw):  # noqa: ANN001
        self.calls += 1
        return RenderResult(
            png=b"\x89PNG", width=100, height=100, console_errors=list(self.console_errors)
        )


# --------------------------- TEXT2HTML ----------------------------------- #
async def test_text2html_success(monkeypatch):
    async def fake(prompt, error_feedback=None):
        return CLEAN

    monkeypatch.setattr(pipeline.llm, "text_to_html", fake)
    art = await pipeline.run_text2html(FakeRenderer(), "hi")
    assert art.kind == "text2html"
    assert art.html == CLEAN


async def test_text2html_retries_then_succeeds(monkeypatch):
    seq = [DIRTY, CLEAN]  # first fails artifact guard, second passes

    async def fake(prompt, error_feedback=None):
        return seq.pop(0)

    monkeypatch.setattr(pipeline.llm, "text_to_html", fake)
    art = await pipeline.run_text2html(FakeRenderer(), "hi")
    assert art.html == CLEAN
    assert seq == []  # both attempts consumed


async def test_text2html_all_invalid_raises(monkeypatch):
    async def fake(prompt, error_feedback=None):
        return DIRTY

    monkeypatch.setattr(pipeline.llm, "text_to_html", fake)
    with pytest.raises(RenderError):
        await pipeline.run_text2html(FakeRenderer(), "hi")


async def test_text2html_rejects_console_errors(monkeypatch):
    async def fake(prompt, error_feedback=None):
        return CLEAN

    monkeypatch.setattr(pipeline.llm, "text_to_html", fake)
    with pytest.raises(RenderError):
        await pipeline.run_text2html(FakeRenderer(console_errors=["boom"]), "hi")


# --------------------------- IMG2HTML ------------------------------------ #
async def test_img2html_gate_skips_correction_when_close(monkeypatch):
    calls = {"correct": 0}

    async def fake_start(img, mt):
        return CLEAN, []

    async def fake_correct(*a, **k):
        calls["correct"] += 1
        return CLEAN, []

    monkeypatch.setattr(pipeline.llm, "start_image_conversation", fake_start)
    monkeypatch.setattr(pipeline.llm, "correct_in_conversation", fake_correct)
    monkeypatch.setattr(
        pipeline.compare,
        "compare",
        lambda *a, **k: CompareResult(overall=0.01, tiles=[], problem_tiles=[]),
    )
    art = await pipeline.run_img2html(FakeRenderer(), b"img", "image/jpeg")
    assert art.kind == "img2html"
    assert calls["correct"] == 0  # cheap gate skipped the paid correction


async def test_img2html_corrects_then_converges(monkeypatch):
    cmp_seq = [
        CompareResult(overall=0.5, tiles=[], problem_tiles=["r1c1"]),  # correct
        CompareResult(overall=0.05, tiles=[], problem_tiles=[]),       # converged
    ]
    calls = {"correct": 0}

    async def fake_start(img, mt):
        return CLEAN, []

    async def fake_correct(messages, render_bytes, render_type, problem_tiles):
        calls["correct"] += 1
        return CLEAN2, messages

    monkeypatch.setattr(pipeline.llm, "start_image_conversation", fake_start)
    monkeypatch.setattr(pipeline.llm, "correct_in_conversation", fake_correct)
    monkeypatch.setattr(pipeline.compare, "compare", lambda *a, **k: cmp_seq.pop(0))
    art = await pipeline.run_img2html(FakeRenderer(), b"img", "image/jpeg")
    assert calls["correct"] == 1
    assert art.html == CLEAN2


async def test_img2html_final_regenerates_on_artifact(monkeypatch):
    regen = {"n": 0}

    async def fake_start(img, mt):
        return DIRTY, []  # initial reply is artifact-laden

    async def fake_regen(messages, reason):
        regen["n"] += 1
        return CLEAN, messages

    monkeypatch.setattr(pipeline.llm, "start_image_conversation", fake_start)
    monkeypatch.setattr(pipeline.llm, "regenerate_clean", fake_regen)
    monkeypatch.setattr(
        pipeline.compare,
        "compare",
        lambda *a, **k: CompareResult(overall=0.01, tiles=[], problem_tiles=[]),
    )
    art = await pipeline.run_img2html(FakeRenderer(), b"img", "image/jpeg")
    assert regen["n"] == 1
    assert art.html == CLEAN


async def test_img2html_final_all_fail_raises(monkeypatch):
    async def fake_start(img, mt):
        return DIRTY, []

    async def fake_regen(messages, reason):
        return DIRTY, messages  # never recovers

    monkeypatch.setattr(pipeline.llm, "start_image_conversation", fake_start)
    monkeypatch.setattr(pipeline.llm, "regenerate_clean", fake_regen)
    monkeypatch.setattr(
        pipeline.compare,
        "compare",
        lambda *a, **k: CompareResult(overall=0.01, tiles=[], problem_tiles=[]),
    )
    with pytest.raises(RenderError):
        await pipeline.run_img2html(FakeRenderer(), b"img", "image/jpeg")

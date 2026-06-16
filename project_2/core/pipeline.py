"""Generation pipeline: TEXT2HTML and IMG2HTML (with iterative correction)."""
from __future__ import annotations

from dataclasses import dataclass

import structlog

from config import settings
from core import compare, llm
from core.render import RenderError, Renderer, validate

log = structlog.get_logger(__name__)

_VALIDATION_RETRIES = 2


@dataclass
class Artifact:
    kind: str  # "text2html" | "img2html"
    html: str
    png: bytes  # final render for preview


async def run_text2html(renderer: Renderer, prompt: str) -> Artifact:
    """Generate HTML from text, validate by rendering, up to 2 retries on error."""
    error: str | None = None
    html = ""
    for attempt in range(_VALIDATION_RETRIES + 1):
        html = await llm.text_to_html(prompt, error_feedback=error)
        try:
            result = await validate(renderer, html)
            log.info("text2html_ok", attempt=attempt)
            return Artifact(kind="text2html", html=html, png=result.png)
        except RenderError as exc:
            error = str(exc)
            log.warning("text2html_invalid", attempt=attempt, error=error)
    raise RenderError(f"text2html failed validation after retries: {error}")


async def run_img2html(
    renderer: Renderer, image_bytes: bytes, media_type: str
) -> Artifact:
    """Reconstruct image as HTML with global iterative correction.

    The correction loop runs as one cached conversation: the original image and
    each prior HTML stay in history, so iterations 2+ re-read them at ~0.1x and
    the current HTML is never re-pasted into the prompt.
    """
    # Step 1: initial reconstruction (opens the conversation).
    html, messages = await llm.start_image_conversation(image_bytes, media_type)
    # Step 2: render.
    result = await renderer.render(html)
    render_png = result.png

    prev_overall = 1.0
    for it in range(settings.img_max_iters):
        # Step 3: diagnostics.
        cmp = compare.compare(
            image_bytes, render_png, settings.img_tile_grid, settings.img_diff_threshold
        )
        log.info(
            "img2html_diag",
            iteration=it,
            overall=round(cmp.overall, 4),
            problems=cmp.problem_tiles,
        )
        # Stop if: already close enough (cheap gate — skip a paid correction),
        # no problem zones, or divergence stopped falling.
        if (
            cmp.overall < settings.img_diff_threshold
            or not cmp.problem_tiles
            or cmp.overall >= prev_overall
        ):
            break
        prev_overall = cmp.overall

        # Step 4: global correction (appends a cached turn to the conversation).
        new_html, messages = await llm.correct_in_conversation(
            messages,
            render_bytes=render_png,
            render_type="image/png",
            problem_tiles=cmp.problem_tiles,
        )
        try:
            new_result = await renderer.render(new_html)
        except RenderError as exc:
            log.warning("img2html_correction_unrenderable", iteration=it, error=str(exc))
            break
        html, render_png = new_html, new_result.png

    # Step 5: final validation — must be a clean standalone document that renders
    # without console errors. On failure (e.g. stray commentary that survived, or
    # a render error), regenerate on the cached conversation and re-check, up to
    # IMG_MAX_ITERS times, before giving up.
    last_err: str | None = None
    for attempt in range(settings.img_max_iters):
        try:
            final = await validate(renderer, html)
            return Artifact(kind="img2html", html=html, png=final.png)
        except RenderError as exc:
            last_err = str(exc)
            log.warning("img2html_final_reject", attempt=attempt, error=last_err)
            html, messages = await llm.regenerate_clean(messages, reason=last_err)
    raise RenderError(f"img2html failed final validation after retries: {last_err}")

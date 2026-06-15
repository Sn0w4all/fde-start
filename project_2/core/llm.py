"""Claude API calls for HTML generation and image-driven correction."""
from __future__ import annotations

import base64
import re

import anthropic
import structlog

from config import settings
from core.retry import with_backoff

log = structlog.get_logger(__name__)

_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

# Network/transient errors worth retrying.
_RETRY_EXC = (
    anthropic.APIConnectionError,
    anthropic.RateLimitError,
    anthropic.InternalServerError,
    anthropic.APITimeoutError,
)

_DISCIPLINE = (
    "Return ONLY a single valid, self-contained HTML document. "
    "All CSS must be inline or inside a <style> tag. "
    "No external resources, no <script>, no CDN links, no markdown fences. "
    "Output must start with <!DOCTYPE html> or <html>."
)

_FENCE_RE = re.compile(r"^\s*```(?:html)?\s*|\s*```\s*$", re.IGNORECASE)


def _strip_markdown(text: str) -> str:
    """Remove ```html ... ``` wrappers if the model added them anyway."""
    text = text.strip()
    if text.startswith("```"):
        text = _FENCE_RE.sub("", text)
    return text.strip()


def _extract_text(message: anthropic.types.Message) -> str:
    parts = [b.text for b in message.content if b.type == "text"]
    return _strip_markdown("".join(parts))


async def _call(system: str, content: list[dict] | str) -> str:
    async def _do() -> str:
        msg = await _client.messages.create(
            model=settings.model,
            max_tokens=8192,
            system=system,
            messages=[{"role": "user", "content": content}],
        )
        return _extract_text(msg)

    return await with_backoff(_do, exc_types=_RETRY_EXC)


def _image_block(image_bytes: bytes, media_type: str) -> dict:
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": base64.standard_b64encode(image_bytes).decode("ascii"),
        },
    }


async def text_to_html(prompt: str, error_feedback: str | None = None) -> str:
    """TEXT2HTML: generate one self-contained HTML file from a text prompt."""
    user = f"Build an HTML page for this request:\n\n{prompt}"
    if error_feedback:
        user += (
            f"\n\nThe previous attempt failed validation with this error:\n"
            f"{error_feedback}\nReturn a corrected full HTML document."
        )
    return await _call(_DISCIPLINE, user)


async def image_to_html(image_bytes: bytes, media_type: str) -> str:
    """IMG2HTML step 1: reconstruct HTML that visually reproduces the image."""
    content = [
        _image_block(image_bytes, media_type),
        {
            "type": "text",
            "text": "Reproduce this image as closely as possible as a web page. "
            "Match layout, colors, typography and spacing.",
        },
    ]
    return await _call(_DISCIPLINE, content)


async def correct_html(
    original: bytes,
    original_type: str,
    render: bytes,
    render_type: str,
    problem_tiles: list[str],
    current_html: str,
) -> str:
    """IMG2HTML step 4: global correction given original, current render, problem zones."""
    zones = ", ".join(problem_tiles) if problem_tiles else "none"
    content = [
        {"type": "text", "text": "ORIGINAL target image:"},
        _image_block(original, original_type),
        {"type": "text", "text": "CURRENT render of your HTML:"},
        _image_block(render, render_type),
        {
            "type": "text",
            "text": (
                f"Problem zones (grid cells where render diverges most): {zones}.\n\n"
                f"Current HTML:\n{current_html}\n\n"
                "Return the FULL corrected HTML document so the render matches the "
                "original more closely. Same discipline: self-contained, no external "
                "resources, no scripts."
            ),
        },
    ]
    return await _call(_DISCIPLINE, content)

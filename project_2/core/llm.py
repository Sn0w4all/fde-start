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


async def _create(messages: list[dict]) -> str:
    """Run a multi-turn create against the cached conversation prefix."""

    async def _do() -> str:
        msg = await _client.messages.create(
            model=settings.model,
            max_tokens=8192,
            system=_DISCIPLINE,
            messages=messages,
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


def _set_single_cache_breakpoint(messages: list[dict]) -> None:
    """Keep exactly one cache_control breakpoint, on the last user content block.

    Prompt caching is a prefix match, so one breakpoint on the latest user turn
    lets every following request re-read the whole prior conversation (original
    image + earlier HTML) at ~0.1x instead of full price.
    """
    for m in messages:
        content = m.get("content")
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    block.pop("cache_control", None)
    # mark the last user message's last content block
    for m in reversed(messages):
        if m.get("role") == "user" and isinstance(m.get("content"), list) and m["content"]:
            last = m["content"][-1]
            if isinstance(last, dict):
                last["cache_control"] = {"type": "ephemeral"}
            return


def _correction_user_content(
    render_bytes: bytes, render_type: str, problem_tiles: list[str]
) -> list[dict]:
    """Correction turn: original image + prior HTML already live in history, so
    we only send the new render + the problem zones (no current_html re-paste)."""
    zones = ", ".join(problem_tiles) if problem_tiles else "none"
    return [
        {"type": "text", "text": "CURRENT render of your previous HTML:"},
        _image_block(render_bytes, render_type),
        {
            "type": "text",
            "text": (
                f"Problem zones (grid cells where the render diverges most from the "
                f"ORIGINAL image shown earlier): {zones}.\n\n"
                "Return the FULL corrected HTML document so the render matches the "
                "original more closely. Same discipline: self-contained, no external "
                "resources, no scripts."
            ),
        },
    ]


async def text_to_html(prompt: str, error_feedback: str | None = None) -> str:
    """TEXT2HTML: generate one self-contained HTML file from a text prompt."""
    user = f"Build an HTML page for this request:\n\n{prompt}"
    if error_feedback:
        user += (
            f"\n\nThe previous attempt failed validation with this error:\n"
            f"{error_feedback}\nReturn a corrected full HTML document."
        )
    return await _call(_DISCIPLINE, user)


async def start_image_conversation(
    image_bytes: bytes, media_type: str
) -> tuple[str, list[dict]]:
    """IMG2HTML step 1: reconstruct HTML from the image and open a conversation.

    Returns (html, messages). The original image stays in ``messages`` so later
    correction turns reuse it from the prompt cache instead of resending it.
    """
    messages: list[dict] = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "ORIGINAL target image:"},
                _image_block(image_bytes, media_type),
                {
                    "type": "text",
                    "text": "Reproduce this image as closely as possible as a web page. "
                    "Match layout, colors, typography and spacing.",
                },
            ],
        }
    ]
    _set_single_cache_breakpoint(messages)
    html = await _create(messages)
    messages.append({"role": "assistant", "content": html})
    return html, messages


async def correct_in_conversation(
    messages: list[dict],
    render_bytes: bytes,
    render_type: str,
    problem_tiles: list[str],
) -> tuple[str, list[dict]]:
    """IMG2HTML step 4: append a correction turn to the existing conversation.

    The original image and the prior HTML are already in ``messages`` (the latter
    as the last assistant turn), so this turn only carries the new render + the
    problem zones — and reads the cached prefix at ~0.1x.
    """
    messages.append(
        {"role": "user", "content": _correction_user_content(render_bytes, render_type, problem_tiles)}
    )
    _set_single_cache_breakpoint(messages)
    html = await _create(messages)
    messages.append({"role": "assistant", "content": html})
    return html, messages

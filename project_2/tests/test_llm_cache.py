"""Unit tests for the cached IMG2HTML conversation helpers (no network)."""
from core.llm import (
    _correction_user_content,
    _image_block,
    _set_single_cache_breakpoint,
)


def _count_breakpoints(messages):
    n = 0
    for m in messages:
        c = m.get("content")
        if isinstance(c, list):
            for b in c:
                if isinstance(b, dict) and "cache_control" in b:
                    n += 1
    return n


def _sample_conversation():
    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "ORIGINAL target image:"},
                _image_block(b"\x89PNG-fake", "image/png"),
                {"type": "text", "text": "Reproduce this image."},
            ],
        },
        {"role": "assistant", "content": "<html>v1</html>"},
        {
            "role": "user",
            "content": _correction_user_content(b"render-bytes", "image/png", ["r1c1"]),
        },
    ]


def test_single_breakpoint_on_last_user_block():
    msgs = _sample_conversation()
    _set_single_cache_breakpoint(msgs)
    assert _count_breakpoints(msgs) == 1
    # it must sit on the last block of the last user message
    assert "cache_control" in msgs[-1]["content"][-1]


def test_breakpoint_is_relocated_not_accumulated():
    msgs = _sample_conversation()
    _set_single_cache_breakpoint(msgs)
    # append another correction turn and re-mark
    msgs.append({"role": "assistant", "content": "<html>v2</html>"})
    msgs.append(
        {"role": "user", "content": _correction_user_content(b"r2", "image/png", ["r2c2"])}
    )
    _set_single_cache_breakpoint(msgs)
    # still exactly one breakpoint, now on the newest user turn
    assert _count_breakpoints(msgs) == 1
    assert "cache_control" in msgs[-1]["content"][-1]


def test_original_image_prefix_is_byte_stable():
    """The original image block must not change across iterations (prefix match)."""
    msgs = _sample_conversation()
    original_data = msgs[0]["content"][1]["source"]["data"]
    _set_single_cache_breakpoint(msgs)
    msgs.append({"role": "assistant", "content": "<html>v2</html>"})
    msgs.append(
        {"role": "user", "content": _correction_user_content(b"r2", "image/png", ["r2c2"])}
    )
    _set_single_cache_breakpoint(msgs)
    # original image data untouched, and carries no cache_control marker
    assert msgs[0]["content"][1]["source"]["data"] == original_data
    assert "cache_control" not in msgs[0]["content"][1]


def test_correction_turn_omits_current_html():
    """Correction turn must not re-paste HTML and must carry exactly one image."""
    content = _correction_user_content(b"render", "image/png", ["r1c2", "r3c1"])
    images = [b for b in content if b.get("type") == "image"]
    assert len(images) == 1  # only the render, not the original
    text = " ".join(b.get("text", "") for b in content if b.get("type") == "text")
    assert "r1c2" in text and "r3c1" in text
    assert "<html" not in text.lower()  # no full HTML re-paste

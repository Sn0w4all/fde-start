"""Pure input-routing logic (kept separate so it is trivially testable)."""
from __future__ import annotations

from enum import Enum


class Route(str, Enum):
    TEXT2HTML = "text2html"
    IMG2HTML = "img2html"
    BOTH = "both"
    EMPTY = "empty"


def route_input(*, has_text: bool, has_image: bool) -> Route:
    """Decide which branch(es) to run from the presence of text / image."""
    if has_text and has_image:
        return Route.BOTH
    if has_image:
        return Route.IMG2HTML
    if has_text:
        return Route.TEXT2HTML
    return Route.EMPTY

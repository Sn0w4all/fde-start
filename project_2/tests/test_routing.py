from bot.routing import Route, route_input


def test_text_only():
    assert route_input(has_text=True, has_image=False) is Route.TEXT2HTML


def test_image_only():
    assert route_input(has_text=False, has_image=True) is Route.IMG2HTML


def test_text_and_image_runs_both():
    assert route_input(has_text=True, has_image=True) is Route.BOTH


def test_empty():
    assert route_input(has_text=False, has_image=False) is Route.EMPTY

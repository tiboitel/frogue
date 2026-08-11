"""Tests for renderer visibility state selection and terminal-size safety."""

from unittest.mock import patch

from frogue.core.fov import Explored, Fov
from frogue.core.level import create_game
from frogue.render.curses_renderer import _cell_state, render


class _StubScreen:
    """Minimal curses screen stub that rejects out-of-bounds writes."""

    def __init__(self, height: int, width: int) -> None:
        self.height = height
        self.width = width
        self.calls: list[tuple[int, int, str]] = []

    def getmaxyx(self) -> tuple[int, int]:
        return self.height, self.width

    def clear(self) -> None:
        pass

    def addstr(self, y: int, x: int, text: str, attr=None) -> None:
        assert 0 <= y < self.height, f"row {y} out of bounds"
        assert 0 <= x < self.width, f"col {x} out of bounds"
        self.calls.append((y, x, text))

    def refresh(self) -> None:
        pass


def _patch_curses():
    return patch.multiple(
        "frogue.render.curses_renderer.curses",
        start_color=lambda: None,
        use_default_colors=lambda: None,
        init_pair=lambda *_: None,
        color_pair=lambda n: n,
    )


def _all_visible(grid: list[list[str]]) -> Fov:
    return Fov({(x, y) for y in range(len(grid)) for x in range(len(grid[0]))})


def test_cell_state_visible() -> None:
    """A cell in Fov should be visible."""
    visible = Fov({(1, 2)})
    explored = Explored({(1, 2)})
    assert _cell_state(1, 2, visible, explored) == "visible"


def test_cell_state_explored() -> None:
    """A cell only in Explored should be explored, not visible."""
    visible = Fov(set())
    explored = Explored({(3, 4)})
    assert _cell_state(3, 4, visible, explored) == "explored"


def test_cell_state_unknown() -> None:
    """A cell in neither set should be None."""
    visible = Fov(set())
    explored = Explored(set())
    assert _cell_state(0, 0, visible, explored) is None


def test_cell_state_no_resources() -> None:
    """With no resources, no cell should be drawn."""
    assert _cell_state(0, 0, None, None) is None


def test_render_small_terminal_no_crash() -> None:
    """Rendering a large grid on a tiny terminal should not raise."""
    runtime, grid, _rooms, _stairs = create_game(seed=1)
    runtime.world.resources.register(_all_visible(grid))
    runtime.world.resources.register(Explored(set()))
    screen = _StubScreen(5, 5)
    with _patch_curses():
        render(screen, runtime.world, grid)
    assert screen.calls


def test_render_status_skipped_when_no_room() -> None:
    """The status line should be skipped when the terminal is too short."""
    runtime, grid, _rooms, _stairs = create_game(seed=1)
    runtime.world.resources.register(_all_visible(grid))
    runtime.world.resources.register(Explored(set()))
    screen = _StubScreen(len(grid), 40)
    with _patch_curses():
        render(screen, runtime.world, grid)
    assert screen.calls
    assert all(y < len(grid) for y, _x, _t in screen.calls)

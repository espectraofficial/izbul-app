from types import SimpleNamespace

import pytest

from ui.layout import (
    calculate_compact_scaling,
    calculate_window_layout,
)
from ui.results_view import ResultsView


@pytest.mark.parametrize(
    ("screen_width", "screen_height"),
    [
        (1280, 720),
        (1366, 768),
        (1920, 1080)
    ]
)
def test_window_layout_stays_inside_common_screen_sizes(
    screen_width,
    screen_height
):
    layout = calculate_window_layout(screen_width, screen_height)

    assert layout.x >= 0
    assert layout.y >= 0
    assert layout.x + layout.width <= screen_width
    assert layout.y + layout.height <= screen_height
    assert layout.width >= layout.min_width
    assert layout.height >= layout.min_height


def test_720p_screen_uses_compact_layout_with_taskbar_space():
    layout = calculate_window_layout(1280, 720)

    assert layout.compact is True
    assert (layout.width, layout.height) == (1126, 620)
    assert layout.y + layout.height == 670


def test_full_hd_screen_keeps_regular_layout():
    layout = calculate_window_layout(1920, 1080)

    assert layout.compact is False
    assert (layout.width, layout.height) == (1440, 860)


def test_macos_layout_reserves_more_space_for_dock():
    layout = calculate_window_layout(
        2048,
        1280,
        reserved_height=150,
        max_height=820
    )

    assert layout.height == 820
    assert layout.y + layout.height < 1280


def test_invalid_screen_dimensions_are_rejected():
    with pytest.raises(ValueError):
        calculate_window_layout(0, 720)


def test_compact_windows_layout_compensates_for_dpi_scaling():
    window_scaling, widget_scaling = calculate_compact_scaling(
        True,
        "win32",
        1.25
    )

    assert window_scaling == pytest.approx(0.8)
    assert widget_scaling == pytest.approx(0.8)


def test_regular_or_non_windows_layout_keeps_default_scaling():
    assert calculate_compact_scaling(
        False,
        "win32",
        1.25
    ) == (1.0, 1.0)
    assert calculate_compact_scaling(
        True,
        "darwin",
        2.0
    ) == (1.0, 1.0)


def test_compact_results_reserve_space_for_logo_and_tree_indent():
    view = SimpleNamespace(
        owner=SimpleNamespace(compact_layout=True)
    )

    widths = ResultsView.get_column_widths(view)

    assert widths["logo"] >= 96
    assert widths["title"] >= 180

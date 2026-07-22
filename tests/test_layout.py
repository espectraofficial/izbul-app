import pytest

from ui.layout import calculate_window_layout


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


def test_invalid_screen_dimensions_are_rejected():
    with pytest.raises(ValueError):
        calculate_window_layout(0, 720)

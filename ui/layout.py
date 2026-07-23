from dataclasses import dataclass


@dataclass(frozen=True)
class WindowLayout:
    compact: bool
    width: int
    height: int
    x: int
    y: int
    min_width: int
    min_height: int


def calculate_compact_scaling(
    compact,
    platform_name,
    dpi_scaling
):
    if (
        not compact or
        platform_name != "win32" or
        dpi_scaling <= 1
    ):
        return 1.0, 1.0

    window_scaling = 1.0 / dpi_scaling
    widget_scaling = min(1.0, 1.0 / dpi_scaling)
    return window_scaling, widget_scaling


def calculate_window_layout(
    screen_width,
    screen_height,
    reserved_height=100,
    max_height=860
):
    if screen_width <= 0 or screen_height <= 0:
        raise ValueError("Screen dimensions must be positive.")

    compact = screen_width < 1400 or screen_height < 850
    available_width = max(900, screen_width - 40)
    available_height = max(
        560,
        screen_height - reserved_height
    )

    width = min(
        1440,
        max(
            min(1080, available_width),
            int(screen_width * 0.88)
        )
    )
    height = min(
        max_height,
        max(
            min(620, available_height),
            int(available_height * 0.9)
        )
    )

    width = min(width, available_width)
    height = min(height, available_height)

    return WindowLayout(
        compact=compact,
        width=width,
        height=height,
        x=max(0, int((screen_width - width) / 2)),
        y=max(20, int((screen_height - height) / 2)),
        min_width=min(1080, available_width),
        min_height=min(620, available_height)
    )

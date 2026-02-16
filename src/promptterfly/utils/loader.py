"""Spiky Loading Animation Utility for Promptterfly"""

import time
from contextlib import contextmanager
from typing import Generator, Optional

from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.style import Style


SPIKY_FRAMES = ['⠁', '⠂', '⠄', '⡀', '⢀', '⠠', '⠐', '⠈']
SPINNER_STYLES = {
    "cyan": {"spinner": "dots", "style": Style(color="cyan", bold=True)},
    "magenta": {"spinner": "line", "style": Style(color="magenta", bold=True)},
    "spiky": {"frames": SPIKY_FRAMES, "interval": 80, "style": Style(color="bright_cyan", bold=True)},
}


class _SpikyLoading:
    def __init__(self, message: str, spinner_style: str = "spiky", console: Optional[Console] = None, color: Optional[str] = None) -> None:
        self.message = message
        self.console = console or Console()
        self._spinner_style = spinner_style
        self._color_override = color
        self._live: Optional[Live] = None

    def _make_spinner(self) -> Spinner:
        style_cfg = SPINNER_STYLES.get(self._spinner_style, SPINNER_STYLES["spiky"])
        if self._color_override:
            style = Style(color=self._color_override, bold=True)
        else:
            style = style_cfg["style"]
        if "frames" in style_cfg:
            return Spinner(style_cfg["frames"], style=style, interval=style_cfg.get("interval", 80))
        else:
            return Spinner(style_cfg["spinner"], style=style, text=self.message)

    def __enter__(self) -> "_SpikyLoading":
        spinner = self._make_spinner()
        self._live = Live(spinner, console=self.console, refresh_per_second=12, transient=True)
        self._live.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._live:
            time.sleep(0.05)
            self._live.stop()
            self._live = None
            self.console.print()


@contextmanager
def spiky_loading(message: str, spinner_style: str = "spiky", console: Optional[Console] = None, color: Optional[str] = None) -> Generator[None, None, None]:
    """
    Display a spiky loading animation while executing a code block.

    Args:
        message: Message to display alongside the spinner.
        spinner_style: Visual theme - "cyan", "magenta", or "spiky" (default).
        console: Rich Console instance (defaults to global console).
        color: Override spinner text color (e.g., "bright_green").

    Example:
        >>> with spiky_loading("Optimizing prompt...")
        ...     result = heavy_computation()
    """
    loader = _SpikyLoading(message, spinner_style, console, color)
    with loader:
        yield


def show_spinner(message: str, spinner_style: str = "spiky", console: Optional[Console] = None, color: Optional[str] = None) -> _SpikyLoading:
    """Imperative-style spinner start (prefer context manager)."""
    return _SpikyLoading(message, spinner_style, console, color)

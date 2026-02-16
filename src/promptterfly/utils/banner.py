"""Banner utilities for Promptterfly REPL."""
import math
import random
from rich.console import Console

console = Console()

# ── colour palette (index → Rich colour name) ──────────────────────────
_PALETTE = {
    1: "bright_white",    # body
    2: "magenta",         # hindwing inner
    3: "cyan",            # forewing inner
    4: "bright_yellow",   # wing spots
    5: "purple",          # wing edge
    6: "bright_yellow",   # antennae
}

_SPARKLE_CHARS  = ["✦", "✧", "·", "⋆", "✶"]
_SPARKLE_COLORS = ["purple", "yellow", "cyan", "magenta", "bright_yellow"]


# ── geometry helper ─────────────────────────────────────────────────────
def _ellipse_dist(x, y, cx, cy, a, b, angle_deg):
    """Normalised squared distance from the centre of a rotated ellipse.

    Returns ≤ 1.0 when (x, y) is inside.
    """
    rad = math.radians(angle_deg)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    dx, dy = x - cx, y - cy
    rx =  dx * cos_a + dy * sin_a
    ry = -dx * sin_a + dy * cos_a
    return (rx / a) ** 2 + (ry / b) ** 2


# ── procedural grid generation ─────────────────────────────────────────
def _generate_grid(width=21, height=17):
    """Build a 2-D grid of palette indices that form a butterfly."""
    grid = [[0] * width for _ in range(height)]
    cx = width // 2                       # centre column

    # ---- body (vertical stripe) ----
    body_top = 4
    for y in range(body_top, height - 1):
        grid[y][cx] = 1

    # ---- antennae (curved outward) ----
    for dx, dy in [(1, -1), (2, -2), (3, -3), (3, -4)]:
        for sign in (1, -1):
            ax, ay = cx + dx * sign, body_top + dy
            if 0 <= ay < height and 0 <= ax < width:
                grid[ay][ax] = 6

    # ---- wing painter ----
    def _fill_wing(ecx, ecy, a, b, angle, c_edge, c_inner, c_spot):
        for y in range(height):
            for x in range(width):
                if grid[y][x]:                       # don't overwrite
                    continue
                d = _ellipse_dist(x, y, ecx, ecy, a, b, angle)
                if d <= 1.0:
                    grid[y][x] = (
                        c_spot  if d <= 0.20 else
                        c_inner if d <= 0.60 else
                        c_edge
                    )

    # forewings  – large, tilted upward
    _fill_wing(cx + 5.5, 7,  5.0, 3.2,   20,  5, 3, 4)
    _fill_wing(cx - 5.5, 7,  5.0, 3.2,  -20,  5, 3, 4)
    # hindwings – smaller, tilted downward
    _fill_wing(cx + 4,  13,  3.8, 2.5,  -15,  5, 2, 4)
    _fill_wing(cx - 4,  13,  3.8, 2.5,   15,  5, 2, 4)

    return grid


# ── rendering ───────────────────────────────────────────────────────────
def _render_grid(grid):
    """Turn a palette-indexed grid into a Rich-markup string.

    Each pixel becomes ``██`` (two full-block chars) so it appears roughly
    square in a typical terminal font.
    """
    lines = []
    for row in grid:
        parts = []
        for cell in row:
            if cell == 0:
                parts.append("  ")
            else:
                colour = _PALETTE[cell]
                parts.append(f"[{colour}]██[/{colour}]")
        lines.append("".join(parts))
    return "\n".join(lines)


def _sparkle_line(width, seed):
    """Return a line of sparsely scattered sparkles *width* columns wide."""
    rng = random.Random(seed)
    parts = []
    for _ in range(width):
        if rng.random() < 0.06:
            ch = rng.choice(_SPARKLE_CHARS)
            co = rng.choice(_SPARKLE_COLORS)
            parts.append(f"[{co}]{ch}[/{co}]")
        else:
            parts.append(" ")
    return "".join(parts)


# ── public API ──────────────────────────────────────────────────────────
def get_butterfly_banner() -> str:
    """Return a procedurally-generated pixel-art butterfly with sparkles."""
    grid      = _generate_grid()
    art       = _render_grid(grid)
    display_w = len(grid[0]) * 2           # "██" per cell

    top = "\n".join(_sparkle_line(display_w, seed=s) for s in (10, 20))
    bot = "\n".join(_sparkle_line(display_w, seed=s) for s in (30, 40))

    return f"{top}\n{art}\n{bot}"


def print_banner():
    """Print the pixel-art butterfly banner to the console."""
    console.print(get_butterfly_banner())

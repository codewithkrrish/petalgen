"""Turning blooms into text.

A Canvas is a grid of (character, color) cells. Blooms are drawn stem-first
so flower heads land on top of stems. to_text() folds the grid into a
string, emitting ANSI codes only where the color actually changes.
"""

from __future__ import annotations

import math

from .flower import Bloom

RESET = "\033[0m"

# Glyphs the petals cycle through — keeps the head from looking like a
# perfect gear, which is the fastest way to spot a generated flower.
PETAL_GLYPHS = ("*", "o", "+", ".")


class Canvas:
    """A width x height grid of characters with optional ANSI colors."""

    def __init__(self, width: int, height: int) -> None:
        if width < 1 or height < 1:
            raise ValueError("canvas dimensions must be positive")
        self.width = width
        self.height = height
        self._chars: list[list[str]] = [[" "] * width for _ in range(height)]
        self._colors: list[list[str | None]] = [[None] * width for _ in range(height)]

    def put(self, x: float, y: float, char: str, color: str | None = None) -> None:
        """Stamp one character. Silently clips anything outside the canvas."""
        ix, iy = int(round(x)), int(round(y))
        if 0 <= ix < self.width and 0 <= iy < self.height and char != " ":
            self._chars[iy][ix] = char
            self._colors[iy][ix] = color or None

    def to_text(self, color: bool = True) -> str:
        """Render the grid to a string, right-trimming each line."""
        lines: list[str] = []
        for y in range(self.height):
            parts: list[str] = []
            active: str | None = None
            for x in range(self.width):
                want = self._colors[y][x] if color else None
                if want != active:
                    if active:
                        parts.append(RESET)
                    if want:
                        parts.append(want)
                    active = want
                parts.append(self._chars[y][x])
            if active:
                parts.append(RESET)
            lines.append("".join(parts).rstrip())
        return "\n".join(lines)


def _draw_stem(canvas: Canvas, bloom: Bloom) -> None:
    palette = bloom.palette
    top = bloom.cy + bloom.head_radius * 0.6
    for step in range(int(top), canvas.height):
        # Gentle S-curve so stems don't look like they were plotted with a ruler.
        x = bloom.cx + bloom.stem_sway * math.sin((step - top) * 0.25)
        canvas.put(x, step, "|", palette.stem)

    # One leaf, a short diagonal off the middle of the stem.
    leaf_y = int(top + (canvas.height - top) * 0.45)
    leaf_x = bloom.cx + bloom.stem_sway * math.sin((leaf_y - top) * 0.25)
    for i in range(1, 4):
        canvas.put(leaf_x + i * bloom.leaf_side, leaf_y - i // 2, "/", palette.leaf)


def _draw_head(canvas: Canvas, bloom: Bloom) -> None:
    palette = bloom.palette

    # Outer ring: one spoke per petal, length jittered per petal.
    for i in range(bloom.petal_count):
        angle = bloom.head_rotation + (2 * math.pi * i) / bloom.petal_count
        length = bloom.head_radius * bloom.petal_lengths[i]
        glyph = PETAL_GLYPHS[i % len(PETAL_GLYPHS)]
        color = palette.petals[i % len(palette.petals)]
        steps = max(2, int(length * 1.5))
        for s in range(1, steps + 1):
            t = s / steps
            # Slight sideways bow so petals curve instead of stabbing straight out.
            bow = math.sin(t * math.pi) * 0.6
            x = bloom.cx + math.cos(angle) * length * t - math.sin(angle) * bow
            # Terminal rows are ~2x as tall as wide, so squash y to keep heads round.
            y = bloom.cy + math.sin(angle) * length * t * 0.5 + math.cos(angle) * bow * 0.5
            canvas.put(x, y, glyph, color)

    # Inner ring: shorter spokes at half-step offsets, brighter color.
    for i in range(bloom.petal_count):
        angle = bloom.head_rotation + (2 * math.pi * (i + 0.5)) / bloom.petal_count
        length = bloom.head_radius * 0.55
        steps = max(2, int(length * 1.5))
        for s in range(1, steps + 1):
            t = s / steps
            x = bloom.cx + math.cos(angle) * length * t
            y = bloom.cy + math.sin(angle) * length * t * 0.5
            canvas.put(x, y, "o", palette.inner)

    # Center: a small dense cluster.
    canvas.put(bloom.cx, bloom.cy, "@", palette.center)
    for dx, dy in ((-1, 0), (1, 0), (0, -0.5), (0, 0.5)):
        canvas.put(bloom.cx + dx, bloom.cy + dy, ".", palette.center)


def draw_garden(canvas: Canvas, blooms: list[Bloom]) -> None:
    """Draw every bloom onto the canvas, stems first so heads sit on top."""
    for bloom in blooms:
        _draw_stem(canvas, bloom)
    for bloom in blooms:
        _draw_head(canvas, bloom)

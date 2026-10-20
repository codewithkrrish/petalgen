"""Growing the flowers: blooms, stems and gardens.

The key idea: everything random comes from one seeded random.Random, so the
same --seed always grows the same garden. A Bloom is just data — where it
sits and how it looks — and rendering lives in render.py, which keeps the
growth logic easy to test without touching ANSI codes.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .palettes import Palette

# Flower heads smaller than this look like blobs, bigger than this eat the
# whole canvas on the default 80-wide terminal.
MIN_HEAD_RADIUS = 3
MAX_HEAD_RADIUS = 7


@dataclass
class Bloom:
    """One flower: position, size and the randomness that shaped it."""

    cx: float
    cy: float
    head_radius: int
    petal_count: int
    head_rotation: float
    # Per-petal multipliers so petals aren't all the same length — real
    # flowers aren't either, and uniform spokes look computer-made.
    petal_lengths: list[float]
    stem_sway: float
    leaf_side: int  # -1 = leaf leans left, 1 = leans right
    palette: Palette


def grow_bloom(
    rng: random.Random,
    palette: Palette,
    cx: float,
    cy: float,
    head_radius: int,
    petal_count: int,
) -> Bloom:
    """Grow a single flower at (cx, cy) using rng for all its randomness."""
    return Bloom(
        cx=cx,
        cy=cy,
        head_radius=head_radius,
        petal_count=petal_count,
        head_rotation=rng.uniform(0, 6.28318),
        petal_lengths=[rng.uniform(0.75, 1.1) for _ in range(petal_count)],
        stem_sway=rng.uniform(-1.5, 1.5),
        leaf_side=rng.choice([-1, 1]),
        palette=palette,
    )


def grow_garden(
    rng: random.Random,
    palette: Palette,
    width: int,
    height: int,
    bloom_count: int,
    petal_count: int,
) -> list[Bloom]:
    """Grow bloom_count flowers spread across the canvas.

    Centers are spaced evenly with a bit of jitter so gardens look planted
    rather than tiled. Heads are kept inside the margins so petals don't
    clip at the canvas edge.
    """
    if bloom_count < 1:
        raise ValueError("bloom_count must be at least 1")
    if not MIN_HEAD_RADIUS <= height // 4 <= MAX_HEAD_RADIUS + 4:
        # Canvas too short for even a small flower to fit comfortably.
        raise ValueError(f"canvas height {height} is too short for a flower")

    blooms: list[Bloom] = []
    head_radius = min(MAX_HEAD_RADIUS, max(MIN_HEAD_RADIUS, height // 6))
    margin = head_radius + 2
    head_y = margin + head_radius

    for i in range(bloom_count):
        # Even spacing with jitter; the +0.5/i+1 bit keeps a single bloom centered.
        slot = width * (i + 1) / (bloom_count + 1)
        jitter = rng.uniform(-width / (bloom_count + 1) / 3, width / (bloom_count + 1) / 3)
        cx = min(max(slot + jitter, margin), width - margin)
        blooms.append(
            grow_bloom(rng, palette, cx, head_y, head_radius, petal_count)
        )
    return blooms

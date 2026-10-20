"""Color palettes for the flowers.

Each palette is just a bundle of ANSI color codes. The mono palette uses
empty codes on purpose, so --palette mono also works as a poor-man's
--no-color on terminals that mangle escape sequences.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    """One named color scheme for a garden."""

    name: str
    description: str
    petals: tuple[str, ...]
    inner: str
    center: str
    stem: str
    leaf: str


def _c(code: int) -> str:
    return f"\033[38;5;{code}m"


PALETTES: dict[str, Palette] = {
    "sunset": Palette(
        name="sunset",
        description="warm oranges and pinks, late-evening garden",
        petals=(_c(208), _c(203), _c(214), _c(198)),
        inner=_c(226),
        center=_c(220),
        stem=_c(64),
        leaf=_c(70),
    ),
    "ocean": Palette(
        name="ocean",
        description="blues and teals, cold-water flowers",
        petals=(_c(75), _c(68), _c(117), _c(45)),
        inner=_c(159),
        center=_c(229),
        stem=_c(36),
        leaf=_c(43),
    ),
    "meadow": Palette(
        name="meadow",
        description="classic wildflower reds, yellows and greens",
        petals=(_c(196), _c(226), _c(202), _c(190)),
        inner=_c(228),
        center=_c(94),
        stem=_c(28),
        leaf=_c(34),
    ),
    "ember": Palette(
        name="ember",
        description="dark reds and ambers, flowers by firelight",
        petals=(_c(124), _c(160), _c(166), _c(130)),
        inner=_c(214),
        center=_c(226),
        stem=_c(58),
        leaf=_c(64),
    ),
    "neon": Palette(
        name="neon",
        description="loud magentas and cyans, arcade bouquet",
        petals=(_c(201), _c(51), _c(213), _c(87)),
        inner=_c(226),
        center=_c(231),
        stem=_c(40),
        leaf=_c(48),
    ),
    "pastel": Palette(
        name="pastel",
        description="soft pinks, lavenders and mints",
        petals=(_c(218), _c(183), _c(189), _c(158)),
        inner=_c(229),
        center=_c(222),
        stem=_c(108),
        leaf=_c(114),
    ),
    "candy": Palette(
        name="candy",
        description="hot pink and white, birthday-cake flowers",
        petals=(_c(199), _c(213), _c(225), _c(205)),
        inner=_c(231),
        center=_c(226),
        stem=_c(71),
        leaf=_c(77),
    ),
    "mono": Palette(
        name="mono",
        description="no color at all, plain ASCII for broken terminals",
        petals=("", "", "", ""),
        inner="",
        center="",
        stem="",
        leaf="",
    ),
}


class UnknownPaletteError(ValueError):
    """Raised when a palette name isn't in PALETTES."""


def get_palette(name: str) -> Palette:
    """Return the palette with this name, or raise UnknownPaletteError."""
    try:
        return PALETTES[name]
    except KeyError:
        known = ", ".join(sorted(PALETTES))
        raise UnknownPaletteError(
            f"unknown palette {name!r} — pick one of: {known}"
        ) from None


def list_palettes() -> list[Palette]:
    """All palettes in a stable order."""
    return [PALETTES[name] for name in sorted(PALETTES)]

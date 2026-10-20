"""Thin CLI for petalgen: parse args, grow a garden, print it.

All the real work lives in flower.py / render.py / palettes.py — this file
just wires arguments to them and handles exit codes.
"""

from __future__ import annotations

import argparse
import os
import random
import sys
import tempfile

from . import __version__
from .flower import grow_garden
from .palettes import UnknownPaletteError, get_palette, list_palettes
from .render import Canvas, draw_garden

MIN_PETALS = 4
MAX_PETALS = 16
MIN_BLOOMS = 1
MAX_BLOOMS = 8
MIN_WIDTH = 40
MAX_WIDTH = 200
MIN_HEIGHT = 10
MAX_HEIGHT = 60


class OutputExistsError(OSError):
    """The --out file already exists and --force wasn't given."""


def build_parser() -> argparse.ArgumentParser:
    """Define the CLI. Kept in its own function so tests can poke at it."""
    parser = argparse.ArgumentParser(
        prog="petalgen",
        description="Grow generative ASCII flowers in your terminal. "
        "Same seed, same garden — every bloom is reproducible.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="random seed; same seed always grows the same garden "
        "(default: random, printed to stderr so you can regrow it)",
    )
    parser.add_argument(
        "--petals",
        type=int,
        default=8,
        help=f"petals per flower, {MIN_PETALS}-{MAX_PETALS} (default: 8)",
    )
    parser.add_argument(
        "--blooms",
        type=int,
        default=3,
        help=f"flowers in the garden, {MIN_BLOOMS}-{MAX_BLOOMS} (default: 3)",
    )
    parser.add_argument(
        "--palette",
        default="sunset",
        help="color palette (default: sunset); see --list-palettes",
    )
    parser.add_argument(
        "--list-palettes",
        action="store_true",
        help="list available palettes and exit",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=80,
        help=f"canvas width, {MIN_WIDTH}-{MAX_WIDTH} (default: 80)",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=24,
        help=f"canvas height, {MIN_HEIGHT}-{MAX_HEIGHT} (default: 24)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="plain ASCII, no ANSI color codes",
    )
    parser.add_argument(
        "--out",
        default=None,
        metavar="FILE",
        help="write the garden to FILE instead of stdout "
        "(refuses to overwrite unless --force)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="allow --out to overwrite an existing file",
    )
    return parser


def _check_range(parser: argparse.ArgumentParser, name: str, value: int, lo: int, hi: int) -> None:
    if not lo <= value <= hi:
        parser.error(f"--{name} must be between {lo} and {hi} (got {value})")


def write_output_atomic(path: str, text: str, force: bool) -> None:
    """Write text to path via temp file + rename, so a crash can't corrupt it.

    Refuses to overwrite an existing file unless force is True.
    """
    if os.path.exists(path) and not force:
        raise OutputExistsError(
            f"{path} already exists — use --force to overwrite it"
        )
    directory = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(directory, exist_ok=True)
    # Temp file in the same directory so os.replace stays on one filesystem.
    fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".petalgen-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            tmp.write(text)
            tmp.write("\n")
        os.replace(tmp_path, path)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def main(argv: list[str] | None = None) -> int:
    """Run the CLI. Returns the process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_palettes:
        for palette in list_palettes():
            print(f"{palette.name:10} {palette.description}")
        return 0

    _check_range(parser, "petals", args.petals, MIN_PETALS, MAX_PETALS)
    _check_range(parser, "blooms", args.blooms, MIN_BLOOMS, MAX_BLOOMS)
    _check_range(parser, "width", args.width, MIN_WIDTH, MAX_WIDTH)
    _check_range(parser, "height", args.height, MIN_HEIGHT, MAX_HEIGHT)

    try:
        palette = get_palette(args.palette)
    except UnknownPaletteError as exc:
        print(f"petalgen: {exc}", file=sys.stderr)
        return 2

    seed = args.seed
    if seed is None:
        seed = random.SystemRandom().randint(0, 999_999)
        print(f"petalgen: grown from seed {seed} — pass --seed {seed} to regrow it",
              file=sys.stderr)

    rng = random.Random(seed)
    try:
        blooms = grow_garden(rng, palette, args.width, args.height, args.blooms, args.petals)
    except ValueError as exc:
        print(f"petalgen: {exc}", file=sys.stderr)
        return 2

    canvas = Canvas(args.width, args.height)
    draw_garden(canvas, blooms)
    text = canvas.to_text(color=not args.no_color)

    if args.out:
        try:
            write_output_atomic(args.out, text, args.force)
        except OutputExistsError as exc:
            print(f"petalgen: {exc}", file=sys.stderr)
            return 1
        except OSError as exc:
            print(f"petalgen: can't write {args.out}: {exc.strerror or exc}", file=sys.stderr)
            return 1
    else:
        print(text)
    return 0

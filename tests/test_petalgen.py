"""Tests for petalgen: growth, rendering, palettes and the CLI."""

import os
import random
import re

import pytest

from petalgen import __version__
from petalgen.cli import OutputExistsError, build_parser, main, write_output_atomic
from petalgen.flower import grow_bloom, grow_garden
from petalgen.palettes import PALETTES, UnknownPaletteError, get_palette
from petalgen.render import Canvas, draw_garden


def _garden(seed=42, **kwargs):
    """Render a small garden to text; the workhorse for most tests."""
    params = dict(width=60, height=20, bloom_count=2, petal_count=6)
    params.update(kwargs)
    palette = get_palette("sunset")
    blooms = grow_garden(random.Random(seed), palette, **params)
    canvas = Canvas(params["width"], params["height"])
    draw_garden(canvas, blooms)
    return canvas.to_text()


# --- growth: deterministic and sane ----------------------------------------

def test_same_seed_grows_same_garden():
    assert _garden(seed=7) == _garden(seed=7)


def test_different_seeds_grow_different_gardens():
    assert _garden(seed=7) != _garden(seed=8)


def test_garden_actually_draws_something():
    text = _garden()
    drawn = [ch for line in text.splitlines() for ch in line if ch not in (" ", "\033")]
    assert len(drawn) > 50  # a 2-flower garden should be mostly flower, not air


def test_grow_garden_rejects_zero_blooms():
    with pytest.raises(ValueError):
        grow_garden(random.Random(1), get_palette("sunset"), 60, 20, 0, 6)


def test_grow_garden_rejects_tiny_canvas():
    with pytest.raises(ValueError):
        grow_garden(random.Random(1), get_palette("sunset"), 60, 6, 1, 6)


def test_bloom_petal_lengths_vary_but_stay_sane():
    bloom = grow_bloom(random.Random(3), get_palette("meadow"), 30.0, 10.0, 5, 8)
    assert len(bloom.petal_lengths) == 8
    assert all(0.7 < length < 1.2 for length in bloom.petal_lengths)
    assert len(set(bloom.petal_lengths)) > 1  # not all identical


# --- rendering --------------------------------------------------------------

def test_canvas_clips_quietly_outside_bounds():
    canvas = Canvas(10, 5)
    canvas.put(-5, -5, "x")
    canvas.put(500, 500, "x")
    assert canvas.to_text() == "\n".join([""] * 5)


def test_canvas_refuses_nonpositive_dimensions():
    with pytest.raises(ValueError):
        Canvas(0, 10)


def test_color_output_contains_ansi_no_color_does_not():
    palette = get_palette("sunset")
    blooms = grow_garden(random.Random(11), palette, 60, 20, 2, 6)
    canvas = Canvas(60, 20)
    draw_garden(canvas, blooms)
    colored = canvas.to_text(color=True)
    plain = canvas.to_text(color=False)
    assert "\033[" in colored
    assert "\033[" not in plain
    # Same drawing underneath the paint: strip ANSI codes and compare.
    stripped = re.sub(r"\033\[[0-9;]*m", "", colored)
    assert stripped == plain


def test_mono_palette_renders_without_escape_codes():
    palette = get_palette("mono")
    blooms = grow_garden(random.Random(5), palette, 60, 20, 2, 6)
    canvas = Canvas(60, 20)
    draw_garden(canvas, blooms)
    assert "\033" not in canvas.to_text()


def test_drawn_lines_respect_canvas_width():
    text = _garden()
    assert all(len(line) <= 60 or "\033[" in line for line in text.splitlines())


# --- palettes -----------------------------------------------------------------

def test_get_palette_unknown_name_suggests_known_ones():
    with pytest.raises(UnknownPaletteError) as excinfo:
        get_palette("not-a-palette")
    assert "sunset" in str(excinfo.value)


def test_every_palette_has_four_petal_colors():
    for palette in PALETTES.values():
        assert len(palette.petals) == 4


# --- CLI ----------------------------------------------------------------------

def test_main_seed_is_reproducible_through_cli(capsys):
    assert main(["--seed", "99", "--no-color", "--width", "60", "--height", "20"]) == 0
    first = capsys.readouterr().out
    assert main(["--seed", "99", "--no-color", "--width", "60", "--height", "20"]) == 0
    assert capsys.readouterr().out == first


def test_main_prints_seed_to_stderr_when_random(capsys):
    assert main(["--no-color", "--width", "60", "--height", "20"]) == 0
    assert "seed" in capsys.readouterr().err


def test_main_rejects_out_of_range_flags():
    for flag, bad in (("--petals", "3"), ("--petals", "17"),
                      ("--blooms", "0"), ("--width", "10"), ("--height", "200")):
        with pytest.raises(SystemExit) as excinfo:
            main([flag, bad])
        assert excinfo.value.code == 2


def test_main_rejects_unknown_palette(capsys):
    assert main(["--palette", "nope"]) == 2
    assert "unknown palette" in capsys.readouterr().err


def test_main_list_palettes(capsys):
    assert main(["--list-palettes"]) == 0
    out = capsys.readouterr().out
    assert "sunset" in out and "mono" in out


def test_main_version_flag():
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0


def test_write_output_atomic_writes_and_replaces(tmp_path):
    target = tmp_path / "garden.txt"
    write_output_atomic(str(target), "bloom", force=False)
    assert target.read_text() == "bloom\n"
    # No stray temp files left behind.
    assert list(tmp_path.iterdir()) == [target]


def test_write_output_atomic_refuses_overwrite_without_force(tmp_path):
    target = tmp_path / "garden.txt"
    target.write_text("precious\n")
    with pytest.raises(OutputExistsError):
        write_output_atomic(str(target), "bloom", force=False)
    assert target.read_text() == "precious\n"  # untouched


def test_write_output_atomic_force_overwrites(tmp_path):
    target = tmp_path / "garden.txt"
    target.write_text("precious\n")
    write_output_atomic(str(target), "bloom", force=True)
    assert target.read_text() == "bloom\n"


def test_main_out_flag_end_to_end(tmp_path, capsys):
    target = tmp_path / "sub" / "garden.txt"  # nested dir gets created
    code = main(["--seed", "5", "--no-color", "--out", str(target),
                 "--width", "60", "--height", "20"])
    assert code == 0
    assert "o" in target.read_text() or "*" in target.read_text()
    # Second run without --force fails cleanly, no traceback.
    assert main(["--seed", "5", "--no-color", "--out", str(target),
                 "--width", "60", "--height", "20"]) == 1
    assert "Traceback" not in capsys.readouterr().err


def test_main_out_flag_unwritable_location(capsys):
    code = main(["--seed", "5", "--no-color", "--out", "/proc/nope/garden.txt"])
    assert code == 1
    assert "Traceback" not in capsys.readouterr().err


def test_version_is_set():
    assert __version__ == "0.1.0"


def test_parser_defaults_match_documented_values():
    args = build_parser().parse_args([])
    assert (args.petals, args.blooms, args.width, args.height) == (8, 3, 80, 24)
    assert args.palette == "sunset" and args.seed is None

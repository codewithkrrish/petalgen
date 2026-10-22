# petalgen

Generative ASCII flowers for your terminal. Give it a seed, get a garden — same seed always grows the same flowers, so you can regrow a favorite. Zero dependencies, pure stdlib.

```
$ petalgen --seed 4242 --no-color --blooms 2 --width 70 --height 22

                                       +
                            +oo*      ooo..
                          oo...oo    *...o*
                           *oo+       .ooo
                             |         +
                             |         |
                             |         |
                             |         |
                          // |      // |
                            /|        /|
                             |         |
```

*(colors won't survive this README — run it in your terminal to see the real thing)*

## Why I built this

I kept seeing generative-art toys that needed npm, a canvas, and twenty minutes of setup. I wanted the opposite: one command, instant flowers, and a seed system so a bloom you like isn't gone forever. It's the kind of thing you run once to smile and keep around for boring terminal sessions.

## Install

```bash
pip install git+https://github.com/codewithkrrish/petalgen.git
```

Or just clone it — there's nothing to compile and no dependencies to install:

```bash
git clone https://github.com/codewithkrrish/petalgen
cd petalgen
python -m petalgen --seed 7
```

Needs Python 3.10+.

## Usage

```bash
petalgen                          # random garden, seed printed to stderr
petalgen --seed 4242              # regrow that exact garden
petalgen --seed 4242 --palette ocean --blooms 5
petalgen --seed 4242 --no-color   # plain ASCII, for pipes and logs
petalgen --seed 4242 --out garden.txt        # save it (won't overwrite)
petalgen --seed 4242 --out garden.txt --force
petalgen --list-palettes
```

Full flags:

| Flag | What it does |
|---|---|
| `--seed N` | random seed; omit it and one is picked and printed so you can regrow the garden |
| `--petals N` | petals per flower, 4–16 (default 8) |
| `--blooms N` | flowers in the garden, 1–8 (default 3) |
| `--palette NAME` | color scheme (default `sunset`) |
| `--list-palettes` | show all 8 palettes |
| `--width N`, `--height N` | canvas size (default 80×24) |
| `--no-color` | strip ANSI codes |
| `--out FILE` | write to a file instead of stdout; refuses to overwrite unless `--force` |

## Palettes

`sunset` `ocean` `meadow` `ember` `neon` `pastel` `candy` `mono`. They're just bundles of ANSI codes in `petalgen/palettes.py` — adding your own is a five-line edit.

## How the seeds work

All randomness comes from a single `random.Random(seed)`: petal lengths, head rotation, stem sway, bloom spacing. Same seed → same garden, byte for byte. Run without `--seed` and the seed gets printed to stderr, so a garden you love is never lost.

## Limitations, honestly

- It's ASCII art. On very narrow terminals (< 40 cols) flowers get clipped — the CLI enforces a minimum width for this reason.
- The y-axis is squashed (terminal rows are ~2x taller than wide), so heads are drawn elliptical to look round. On square-cell renderers they'll look slightly wide.
- Colors are 256-color ANSI. Ancient terminals will show escape garbage — that's what `--palette mono` / `--no-color` is for.

## Project structure

```
petalgen/
  __init__.py    version
  __main__.py    `python -m petalgen` entry point
  cli.py         argument parsing, exit codes, atomic file writes
  flower.py      growth logic: blooms, stems, garden layout (seeded)
  palettes.py    the 8 color palettes
  render.py      canvas grid -> ANSI/plain text drawing
tests/
  test_petalgen.py   26 tests: determinism, palettes, CLI, edge cases
```

## License

MIT — see [LICENSE](LICENSE).

Made by [Krrish](https://github.com/codewithkrrish).

# Wondrous Magic — English translation

Reverse engineering and translation work for *Wondrous Magic* (ワンドラスマジック),
Super Famicom, ASCII / System Sacom, 1993.

## State

| Area | Status |
|---|---|
| Text engine | Reverse engineered, patched to half-width |
| Character table | Complete — 192 text glyphs, 256 kanji, read out of the ROM font |
| Script extraction | Complete — 920 strings across five blocks |
| Compression | RUX and a second LZSS, both decoded; RUX compressor written |
| Title screen, name entry, intro crawl | Translated |
| Block C — menus, places, classes, spells | Translated |
| Block A — 151 items with descriptions | Translated |
| Block B — story script | **Translated, all 412 strings** |
| Block D — Rinkle's area hints | Translated, 51 strings |
| Block E — status screen layout | Tokens only, nothing to translate |
| World map nameplates | Extracted as PNGs — baked art, not yet redrawn |
| Monster names | Decoded — 63 names, font and table found, not yet converted |

Blocks B and D are repacked against their pointer tables at build time, so their
strings are not limited to their original lengths. Blocks A, C and E are written
in place and must fit.

## Build

    python3 build/build.py

Needs Python 3 and Pillow. Put the Japanese ROM in `rom/` first (see `rom/README.md`).
Output is `rom/Wondrous_Magic_EN.sfc`. Needs `openpyxl` — the build reads the
workbook directly.

The build is a single pass from a clean ROM — no incremental state, no patch order
to remember. Every stage asserts the bytes it is replacing, so a wrong ROM or a
double-applied patch fails loudly instead of producing something subtly broken.

## Layout

    docs/        what the game does and how
    tools/       standalone: disassembler, decompressor, script dumper, font sheet
    build/       the patch chain
    data/        extracted script, character table, translation spreadsheet
    assets/      font sheets, editable and reference

## Where the text is

| Block | ROM | Strings | Contents |
|---|---|---:|---|
| C | `$090000-$090EF6` | 138 | menus, config, status windows |
| A | `$0912C0-$092FDF` | 305 | items, spells, equipment |
| D | `$09316E-$093943` | 51 | Rinkle's area hints |
| B | `$098340-$0A5625` | 412 | story script |
| E | `$08D023-$08D08E` | 14 | status screen layout, bank `$91` |
| system | `$141000-$141272` | 14 | title menu, name entry, save/load |
| crawl | RUX archive `$132000` | 2 | intro poem, prologue |

Not script, and not in any block: the world map nameplates and the battle monster
names. See `docs/assets.md`.

`data/Wondrous_Magic_script.xlsx` **is** the script — the only place English is
authored. There are no `script_*.py` tables any more; `build/sheet.py` reads the
workbook and hands the build what it used to import. See `docs/translating.md`.

## Reading order

Start with `docs/handoff-prompt.md` is a ready-made brief for translating block B in a
fresh session. `docs/text-engine.md` — everything else depends on the descriptor
format. Then `docs/fonts.md` for the three fonts and who reads which,
`docs/screens.md` for the title and name entry, `docs/compression.md` for RUX,
and `docs/memory-map.md` for the full list of patch sites. `docs/assets.md`
covers the two things that look like text but are graphics.

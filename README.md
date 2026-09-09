# Wondrous Magic — English translation

Reverse engineering and translation work for *Wondrous Magic* (ワンドラスマジック),
Super Famicom, ASCII / System Sacom, 1993.

## State

| Area | Status |
|---|---|
| Text engine | Reverse engineered, patched to half-width |
| Character table | Complete — 192 text glyphs, 256 kanji, read out of the ROM font |
| Script extraction | Complete — 920 strings across five blocks |
| Compression | RUX and a second LZSS, both decoded, both compressors written |
| Title screen, name entry, intro crawl | Translated |
| Block C — menus, places, classes, spells | Translated |
| Block A — 151 items with descriptions | Translated |
| Block B — story script | **Translated, all 412 strings** |
| Block D — Rinkle's area hints | Translated, 51 strings |
| Block E — status screen layout | Tokens only, nothing to translate |
| World map nameplates | **English** — all twenty redrawn, compiled from PNGs |
| Monster names | **English** — Latin font, 12-character names, renderer patched |

Blocks B and D are repacked against their pointer tables at build time, so their
strings are not limited to their original lengths. Blocks A, C and E are written
in place and must fit.

## Build

    pip install pillow odfpy
    python3 build/build.py

Put the Japanese ROM in `rom/` first — see `rom/README.md`. Output is
`rom/Wondrous_Magic_EN.sfc`. Pillow draws the fonts; odfpy reads the workbook,
which the build reads directly rather than through any generated table.

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
names. The names are English now and are authored on the `Monster names` sheet.
The nameplates are art — `assets/plates/NN_Name.png`, one file per plate, compiled
into the ROM on every build, so changing one means editing the PNG. All twenty
are drawn in English, and the two blocks they pack into have only about forty
bytes to spare, so a redraw that adds detail can overrun. See `docs/assets.md`.

`data/Wondrous_Magic_script.ods` **is** the script — the only place English is
authored. There are no `script_*.py` tables any more; `build/sheet.py` reads the
workbook and hands the build what it used to import. See `docs/translating.md`.

## Reading order

`docs/text-engine.md` first — everything else depends on the cell descriptor
format and the half-width scheme. Then:

| Doc | For |
|---|---|
| `docs/translating.md` | how the workbook drives the build, and the rules for writing |
| `docs/memory-map.md` | blocks, pointer tables, patch sites, debugging notes |
| `docs/fonts.md` | the fonts and which code reads which |
| `docs/compression.md` | RUX and the second LZSS |
| `docs/screens.md` | title screen and name entry |
| `docs/assets.md` | the nameplates and monster names — graphics, not script |

Every asset and every block is English now. What is left is playing it: the
build has never been checked past the point where each piece was verified on its
own.

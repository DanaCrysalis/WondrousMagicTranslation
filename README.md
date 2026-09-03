# Wondrous Magic — English translation

Reverse engineering and translation work for *Wondrous Magic* (ワンドラスマジック),
Super Famicom, ASCII / System Sacom, 1993.

## State

| Area | Status |
|---|---|
| Text engine | Reverse engineered, patched to half-width |
| Character table | Complete — 192 text glyphs, 256 kanji, read out of the ROM font |
| Script extraction | Complete — 2,884 strings across three blocks |
| Compression (RUX) | Decompressor and compressor, both verified |
| Title screen | Translated |
| Name entry | Translated, names round-trip into dialogue |
| Intro poem and prologue | Translated |
| Opening dialogue scene | Translated (proof of concept) |
| Dictionary compression | `$1E nn` escape, 512 slots, 444 used |
| Block C — menus, places, classes, spells | Translated |
| Block A — 151 items with descriptions | Translated |
| Block B — story script | Opening arc translated, 13 of 412 strings |

## Build

    python3 build/build.py

Needs Python 3 and Pillow. Put the Japanese ROM in `rom/` first (see `rom/README.md`).
Output is `rom/Wondrous_Magic_EN.sfc`, checksum `$1853`.

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
| A | `$0912C0-$0976C5` | 2334 | items, spells, equipment |
| B | `$098340-$0A5625` | 412 | story script |
| system | `$141000-$141272` | 14 | title menu, name entry, save/load |
| crawl | RUX archive `$132000` | 2 | intro poem, prologue |

`data/Wondrous_Magic_script.xlsx` holds blocks A, B and C with a glossary sheet.
Translate into the English column; `tools/wmtool.py` re-encodes.

## Reading order

Start with `docs/handoff-prompt.md` is a ready-made brief for translating block B in a
fresh session. `docs/text-engine.md` — everything else depends on the descriptor
format. Then `docs/fonts.md` for the three fonts and who reads which,
`docs/screens.md` for the title and name entry, `docs/compression.md` for RUX,
and `docs/memory-map.md` for the full list of patch sites.

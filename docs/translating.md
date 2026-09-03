# Translating

## Blocks A, B and C

`data/Wondrous_Magic_script.xlsx` — 2,884 rows, one per string.

| Column | |
|---|---|
| ID / ROM / CPU | where the string lives |
| Bytes | original size; stay at or under it for in-place insertion |
| Japanese | decoded, with control codes as `<...>` tokens |
| English | type here |
| Raw hex | the original bytes |

Rules:

- Keep every `<...>` token, in order. They are engine commands, not decoration.
- Check the Glossary sheet before inventing a rendering.
- A dialogue box is 14 cells wide, which at half-width is **28 characters** per
  line. Break lines to fit that, not to match the Japanese.
- English costs roughly one byte per character with the half-width engine. Block B
  strings must fit their original length — block B's pointers have not been
  located, so strings cannot be relocated or resized yet.

`tools/wmtool.py` has `decode()`, `text()` and `encode()` for round-tripping.
`encode()` accepts kanji and emits `$1E xx`.

## Block A

`build/script_a.py` holds only two hand-written tables — `NAMES` (151 items) and
`TAILS` (114 description bodies). `build()` walks the block and assembles each
description from the English name, the original icon run, and the tail, so the
150-odd description strings never have to be written out.

The description's first line is the name padded to the width the Japanese name
and its padding occupied, then the stat icons. Where an English name will not fit
that width the icons simply shift left; the builder only asserts the line stays
inside the 14-cell window. Full-width `＋`, `−` and `？` in the icon run are
mapped to ASCII, which buys back half a cell each.

## Block B

`build/script_b.py`, keyed by ROM offset. Block B is 412 strings, 42,219 Japanese
characters over 4,681 lines — a novel's worth of dialogue, translated in passes.
Anything absent from the dict is left in Japanese, which the engine renders as
ASCII nonsense, so an untranslated scene is obvious rather than subtly wrong.

Strings must fit their original byte length: block B's addresses are computed
somewhere I have not found, so nothing can be relocated or resized. The
dictionary is what makes that possible — English runs about 1.4x the Japanese
character count here, and compression more than covers it.

Four text rows per box, 28 half-width characters per line. Put the speaker on its
own line, then at most three lines before a `<WAIT>`; a fifth line scrolls the
first away.

## The intro crawl

`build/prologue_patch.py`, lists `POEM` and `PROLOGUE`. Up to 32 characters a
line, cut at column 16 into two records of 16 glyphs. Both sections must keep
their exact byte length; the builder pads with blank rows and asserts.

Pairs are generated automatically from whatever text you write.

## Title screen and name entry

`build/systext.py`, dict `STRINGS`. Each entry is rewritten inside its original
byte length, so keep them short — the builder asserts if a string will not fit.

`CHART_ROWS` is the name entry grid. Row lengths must not change; the builder
preserves the symbol buttons parked at the ends of the last two rows.

## The font

Export, edit, rebuild:

    python3 tools/font_tool.py                 # writes assets/halfwidth_font_sheet.png
    # edit the sheet, keeping it 128x96
    # then load it in build/build.py in place of the generated font

Geometry and colours are documented in `docs/fonts.md`. The build currently
renders the font from a TTF; swapping in a hand-drawn sheet means calling
`font_tool.load()` instead of `write_halfwidth_font()`.

## Dictionary compression

English does not fit the original byte budgets. Japanese kana carry a whole
syllable per byte, so a literal translation of a block C string runs two to three
times its original size — 86 of 103 strings overflowed on the first pass.

`$1E` used to be the kanji escape. With the script in ASCII the kanji bank is
dead, so `$1E nn` now prints **dictionary entry nn** by re-entering the
interpreter at `$954F`, the same way `$02` prints a name. Any word costs two
bytes however long it is.

    $3E:A000   512 x uint16 pointer table    ROM $1F2000
    $3E:A400   entries, $00 terminated       ROM $1F2400

Slots 0-254 are reached with `$1E nn` at two bytes. Slot 255 is an escape: `$1E
$FF nn` reaches slots 256-511 at three bytes. `build/dictionary.py` picks entries
greedily by bytes saved, then `fit()` forces extra entries until every string is
under budget. Forced entries go to the *front* of the list so they land in the
cheap bank — the strings that need one are exactly those with no budget to spare.
Blocks A, B and C together use 444 entries and 4,764 bytes.

Consequence: any **untranslated** Japanese string still containing `$1E xx` now
expands a dictionary entry instead of drawing a kanji. Harmless — entries are
valid strings and terminate — but untranslated text looks wrong in a new way.

## Window rows

Menu windows are drawn inline with the `$E8-$FF` frame codes and rows must come
out to a whole number of cells, since half-width letters are half a cell each.
The main menu is 11 cells of content between the frame pieces (22 half-width
characters); the config windows are 14 (28 characters). `build/build.py` asserts
this.

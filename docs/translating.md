# Translating

## Blocks A, B and C

`data/Wondrous_Magic_script.xlsx` — 2,884 rows, one per string.

The workbook is **generated**, not authored. `python3 tools/make_spreadsheet.py`
rebuilds it from the ROM and the three script modules, so it can never drift from
what is actually inserted. Editing a cell will not change the ROM — put the
English in `build/script_a.py`, `script_b.py` or `script_c.py` and regenerate.

| Column | |
|---|---|
| ID / ROM / CPU | where the string lives |
| Bytes | original size; stay at or under it for in-place insertion |
| Status | `done` if this string is inserted |
| Japanese | decoded, with control codes as `<...>` tokens |
| English | green where inserted, yellow where still open |
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

## Display width, not just bytes

Two limits apply and they are independent. The **byte budget** is what the string
must fit in the ROM, and the dictionary buys headroom there. The **display width**
is what the window can show, and no amount of compression helps:

    dialogue box       14 cells   28 half-width characters
    map nameplate       5 cells   10 half-width characters
    menu window rows   11 or 14 cells, and must come out whole

`build/build.py` asserts the nameplate and the menu rows. Where a name will not
fit, use a manufactured glyph rather than truncating — `<G80>` is a house, and
the place names use it for "X's house".

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

`$0E nn` prints **dictionary entry nn** by re-entering the interpreter at
`$954F`, the same way `$02` prints a name. Any word costs two bytes however long
it is.

It was originally on `$1E`, the kanji escape, and that was a mistake: untranslated
Japanese is full of `$1E xx`, so every untranslated string expanded whole English
phrases mid-sentence and overran its window - the village exit sign read "I love
this village" and leaked letters across the map. `$0E` was unhandled by the
original engine, so nothing in the script uses it. `$1E` now consumes its
argument and draws nothing, and the comparison `$0E` took over was `$01`, a
no-op, so untranslated strings containing `$01` end early instead of looping.

    $3E:A000   768 x uint16 pointer table    ROM $1F2000
    $3E:A600   entries, $00 terminated       ROM $1F2600

Slots 0-253 are reached with `$0E nn` at two bytes. Slots 254 and 255 are
escapes: `$0E $FF nn` reaches 256-511 and `$0E $FE nn` reaches 512-767, both at
three bytes. `build/dictionary.py` picks entries
greedily by bytes saved, then `fit()` forces extra entries until every string is
under budget. Then `reorder()` ranks every entry by the smallest budget that references it, so
the entries a three-byte string depends on land in the cheap bank — a three-byte
budget can only afford a two-byte reference. Ranking moves entries between banks
and can push a string that fitted back over, so the two steps run alternately
until nothing overflows. Blocks A, B and C together use 599 entries and 7,908
bytes.

Consequence: any **untranslated** Japanese string still containing `$1E xx` now
expands a dictionary entry instead of drawing a kanji. Harmless — entries are
valid strings and terminate — but untranslated text looks wrong in a new way.

## Window rows

Menu windows are drawn inline with the `$E8-$FF` frame codes and rows must come
out to a whole number of cells, since half-width letters are half a cell each.
The main menu is 11 cells of content between the frame pieces (22 half-width
characters); the config windows are 14 (28 characters). `build/build.py` asserts
this.

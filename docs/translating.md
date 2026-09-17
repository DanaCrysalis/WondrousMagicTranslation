# Translating

## The workbook is the script

`data/Wondrous_Magic_script.ods` — 921 rows in `Script`, one per string, plus the
sheets that hold everything else. It is OpenDocument, so LibreOffice, Excel and
Google Sheets all open it; `build/book.py` reads and writes it through odfpy.

It is the **only** place English is authored. There are no `script_a.py`,
`script_b.py` or `script_c.py` tables any more, and no hand-written STRINGS or
POEM lists either. `build/sheet.py` reads the workbook and hands the build the
dicts it used to import.

| Sheet | Holds | Authored? |
|---|---|---|
| Script | every ROM string, blocks A B C | English column, blocks B and C |
| Item names | 151 block A item names | yes |
| Descriptions | 114 block A description bodies | yes |
| Monster names | 63 battle names | yes, 12 ASCII characters each |
| Title screen | title, save and options strings | yes |
| Name entry | the name entry grid | yes |
| Intro crawl | the opening poem and prologue | yes |
| Glossary | agreed renderings | yes |
| Questions | open calls for the translator | yes |
| Control codes | token reference | generated |

Two things are generated and will be overwritten, so do not edit them:

- **The block A English column.** Descriptions are assembled from the item name,
  the icon run copied verbatim out of the original ROM string, and the
  description body. Edit `Item names` and `Descriptions` instead. Those cells are
  shaded grey.
- **Everything to the left of English** — ID, ROM, CPU, Bytes, Japanese, Raw hex.
  `tools/refresh_spreadsheet.py` rewrites them from the ROM.

### Working on it

    python3 tools/check_script.py          # tokens, width, ASCII, rough budget
    python3 build/build.py                 # the real byte budgets
    python3 tools/refresh_spreadsheet.py   # only after the ROM columns go stale

`refresh_spreadsheet.py` matches rows by ROM offset and never touches authored
English, so it is safe to run at any time. It replaces the old
`make_spreadsheet.py`, which generated the workbook from the modules — the
opposite direction.

Rules:

- Keep every `<...>` token, in order. They are engine commands, not decoration.
  `check_script.py` will catch a dropped one.
- Check the Glossary sheet before inventing a rendering; log anything you had to
  guess on the Questions sheet.
- A dialogue box is 14 cells wide, which at half-width is **28 characters** per
  line. Break lines to fit that, not to match the Japanese.
- English costs roughly one byte per character with the half-width engine. Block B
  strings must fit their original length — block B's pointers have not been
  located, so strings cannot be relocated or resized yet.

`tools/wmtool.py` has `decode()`, `text()` and `encode()` for round-tripping.
`encode()` accepts kanji and emits `$1E xx`.

### The one thing a spreadsheet is bad at

Trailing spaces. The `Name entry` grid rows must be exactly 14, 14, 14, 14, 14,
0, 13 and 12 cells, and some of those cells are spaces; an editor that trims them
silently breaks the grid. `systext.py` asserts the lengths on import rather than
trusting them, and the sheet carries a Length column so you can see it go wrong.
The same applies to the single leading space on continuation lines in dialogue.

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

## The trailing newline

608 of the 868 strings end `$0D $00` in the ROM - a newline, and then the
terminator. It is not decoration. It leaves the cursor at the start of the next
row, so the next string drawn into the same window starts where it should.
Bare item names, which are printed inline in the middle of a sentence, do not
have one; anything that occupies a line of its own does.

The workbook does not carry it, and should not: the extractor strips it, and a
trailing blank line in a spreadsheet cell would not survive being edited.
`sheet.text()` puts it back, on every string whose Japanese original has one.
So **do not end an English cell with a blank line** - it is added for you, and
what the sheet says is still what appears.

Without it, every string handed the next one a cursor halfway along a line. That
is what put "Welcome to my shop!" and "What can I get you?" on the same row.

## Covering, not just fitting

A third limit, and the one that is easiest to miss: **a line in a window that is
not cleared must be at least as wide, in cells, as the Japanese line it
replaces.**

Menu and shop windows are never cleared between one string and the next. They
did not need to be. Every Japanese glyph was one whole cell, so each line
physically covered the line before it and left the cursor where the next string
expected to start. Half-width English covers half as much per character, so a
narrower line leaves the tail of the last one on screen, and the next string
starts in the wrong column. That is one bug, and it looks like several:

    Welcome to my shop!        ran into "What can I get you?" on the same row
    Item Storage, Appraiser    kept stale words from the previous prompt
    Temple                     the same
    Use Item                   kept the m of "Drop Item" behind it

Pad with `　`, the full-width space: one whole cell, and one byte. A plain
space is half a cell, so a half-cell shortfall takes one space and then
full-width spaces. Never pad past the Japanese width - the window is only so
wide, and the cursor wraps onto the same row rather than the next one.

### Never pad a line whose width is decided at runtime

`Sell the <NAME:0301>?` is not nine cells wide. `<NAME:sWW>` pads *up* to WW
cells and grows straight past it when the name needs more, and which item it is
is not known until the game runs - "Wooden Staff" is six cells where the field
declares one. So that line is 11.5 cells, not 9.

The Japanese sized these lines so the longest name just fits. There is nothing
spare to pad, and padding them can only overflow: three cells added to that line
took it to 14.5, and the half cell past the window is the right border, which
duly disappeared. Leave any line carrying a `<NAME>` field alone.

    python3 tools/check_cover.py

lists every line that is short. It is a report, not a gate: the spell names are
short on purpose, because they are printed inline in battle as well as in the
menu, where the menu's own name field pads them. It also flags, with `!!`, any
line whose worst case - every field at its longest - would run past the
fourteen-cell window.

## The intro crawl, again

The Japanese crawl is double-spaced - a blank row after every single line - and
centred. In English, at thirty characters a line rather than fourteen glyphs,
the double spacing just spreads it thin, so only the paragraph breaks are kept:
**a blank row on the `Intro crawl` sheet is a paragraph break**, and
`build/prologue_patch.py` does the centring. Centring is to an even column,
because a cell is a pair of letters and an odd shift re-pairs every letter on
the line and mints a new glyph for each one.

## Block A

151 items, each a short name string followed by a description string. The
description's first line repeats the name, padded, then carries stat icons
(`<S36>` `<S37>` `<S38>`) and their values; the rest is the usage or equip
restriction.

Only two tables are written by hand, and both are now sheets: `Item names` and
`Descriptions`. `sheet.block_a()` walks the block and assembles each description
from the English name, the original icon run, and the body, so the 150-odd
description strings never have to be written out. 114 distinct bodies cover all
151 descriptions.

The description's first line is the name padded to the width the Japanese name
and its padding occupied, then the stat icons. Where an English name will not fit
that width the icons simply shift left; the builder only asserts the line stays
inside the 14-cell window. Full-width `＋`, `−` and `？` in the icon run are
mapped to ASCII, which buys back half a cell each.

## Block D — the area hints

51 strings at `$09316E`, Rinkle's monster-by-monster advice, reached through a
51-entry table at `$0930F7` of absolute `$92:xxxx` addresses. `build/blockd.py`
repacks them across two extents — their own slot and the free `$0976C5-$098000`
after block A — so length is not a constraint. English runs about 1.5x here,
which the original 2,005-byte slot would not take.

## Block E — the status screen

14 strings at `$08D023`, in bank `$91`, reached by literal `LDA #$11 / LDX #$D0xx`
so they cannot move. They hold only `<C09>` cursor positions, `<S33>`-`<S3A>`
stat icons, `<NUM7>` fields and the word `Lev.` — nothing to translate. Two of
them held a full-width slash `$D9` for the health separator, patched to `$2F`.

Every field on that screen is positioned in whole cells while the digits inside
are half-width, so labels abutting a number want an even character count.

## Blocks B and C

Authored directly in the `Script` sheet: what is in the English column is what
gets inserted. Block B is 412 strings, 42,219 Japanese characters over 4,681
lines. It is complete except for `$098340`, which is two bytes (`0D 00`) and
holds no text. Block C is menus, windows and status text.

Anything left blank stays Japanese, which the engine renders as ASCII nonsense,
so an untranslated string is obvious rather than subtly wrong.

Strings must fit their original byte length: block B's addresses are computed
somewhere I have not found, so nothing can be relocated or resized. The
dictionary is what makes that possible — English runs about 1.4x the Japanese
character count here, and compression more than covers it.

Four text rows per box, 28 half-width characters per line. Put the speaker on its
own line, then at most three lines before a `<WAIT>`; a fifth line scrolls the
first away.

## The intro crawl

`build/prologue_patch.py` reads the `Intro crawl` sheet. Up to 32 characters a
line, cut at column 16 into two records of 16 glyphs. Both sections must keep
their exact byte length; the builder pads with blank rows and asserts.

Pairs are generated automatically from whatever text you write.

## Title screen and name entry

`build/systext.py` reads the `Title screen` and `Name entry` sheets. Each title
string is rewritten inside its original byte length, so keep them short — the
builder asserts if a string will not fit.

`Name entry` is the grid. Row lengths must not change; the builder preserves the
symbol buttons parked at the ends of the last two rows, and asserts the lengths
on import.

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

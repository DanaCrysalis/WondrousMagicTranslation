# Fonts

Three fonts now, where the original had one. Splitting them was what let the
dialogue go English without breaking the title screen and name entry, which read
the Japanese font directly.

## Japanese font — ROM `$0A8000`, 448 glyphs

16×16, 2bpp, uncompressed. Glyph `g` at

    $0A8000 + (g >> 3) * $200 + (g & 7) * 32

with 32 bytes there (top-left then top-right tile) and 32 more at `+$100`
(bottom-left, bottom-right). Colours 0, 1 and 3 only — 1 is the shadow.

    g $000-$0BF   text bank    script bytes $20-$DF
    g $0C0-$1BF   kanji bank   script $1E xx

Character table in `data/table.json`, sheets in `assets/font_text_bank.png` and
`assets/font_kanji_bank.png`.

Hiragana sit at `$21-$4E` in plain gojūon order. Katakana are **not** parallel:
the order runs `...ヤユヨ ワヲン ラリルレロ`, unlike the hiragana block. Getting
that wrong makes every name misread — リンクル comes out as ロルクワ, エルフ as
エワフ.

In the English build the text bank holds single Latin letters and the kanji bank
holds letter pairs. See `screens.md`.

## One sheet, three fonts

`assets/halfwidth_font_sheet.png` is the single source. `build/glyphs.py` loads
it and every font in the build is derived from it, so the dialogue, the intro
crawl and the title screen cannot drift apart:

    half-width   $3E:9000   8x16, one glyph per cell     dialogue engine
    pairs        $27:8000   16x16, two letters per cell  intro crawl
    pairs        $0AB000    16x16, two letters per cell  menus and prompts
    singles      $0A8000    16x16, one letter centred    name entry chart

Redraw the sheet and rebuild; nothing else needs touching.

## Half-width ASCII — ROM `$1F1000` (`$3E:9000`), 97 glyphs

8×16, 2bpp, 32 bytes per glyph: top tile then bottom tile, linear at `g * 32`.
Glyph `h` draws ASCII `h + $1F`. `h = 0` is "cell not written" and `h = 96` is the
half-width space; both blank.

Read only by `COPYCELL` in the patched dialogue engine.

`tools/font_tool.py` exports the sheet and a magnified guide back out of a built
ROM, which is how to check an import landed.

`assets/halfwidth_font_sheet.png` is the editable one — 128×96, 16 columns × 6
rows of 8×16 cells, no gaps, index = `row*16 + column`. Three colours: `#000000`
background, `#808080` shadow, `#FFFFFF` body; anything else snaps to the nearest
by brightness. `halfwidth_font_guide.png` is a magnified reference, not an input.

## Manufactured glyphs

The descriptor carries a 7-bit glyph index, so `h` runs to 127 and the font
region reaches `$1F1FE0` — just short of the dictionary table. `h` 1-95 come from
the sheet; anything above is drawn in code, in `SYMBOLS` in `build/glyphs.py`.

Script byte is `h + $1F`, so these sit at `$80` upward and are written `<G80>`.
So far there is one: a house, because the world map nameplate holds only ten
half-width characters and "Cruel's house" is thirteen — the overflow wrapped a
stray letter onto the next line.

## Intro crawl pair font — ROM `$138000` (`$27:8000`)

16×16 in the same split layout as the Japanese font, each glyph holding two
half-width letters from the sheet. 170 glyphs, generated at build time from the
crawl text.

The crawl renderer corrupts the last glyph of a record once a record exceeds about
eight glyphs, so it cannot be converted to half-width the way the dialogue engine
was — it needs sixteen glyphs per record to fill a row. Pairs keep the original
eight-glyph records and the original timing, and still give 32 characters per row.

Pairs work here and not in dialogue because the crawl is fixed text. Dialogue has
to render the player's name and decimal numbers, composed at runtime, which no
pair font can do.

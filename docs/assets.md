# Assets that are not script

Two things look like text in the game but are not in any text block: the world
map nameplates, and the monster names in battle. Both cost a lot of time to find,
so the trail is written down here.

Neither is reached by the dialogue engine. Both live in LZSS blocks — see
`compression.md` — which is why searching the ROM for their script bytes, their
glyph indices, or their tiles all came back empty.

## World map nameplates

**Baked art.** Twenty location banners, drawn in the same typeface as the
Japanese font but redrawn with an outline, so there is no string to translate.
Compared against the font glyph for 魔, the closest plate character differs in 34
of 256 pixels.

    ROM $0B3D68   LZSS, $2800 -> $7E:4000    Sheloon .. Steel
    ROM $0B4A1E   LZSS, $2800 -> $7E:6800    Darles .. Temple of Shrell

Both blocks hold 16×16 characters in the Japanese font's own arrangement: eight
characters to a `$400` block, top halves first, bottom halves `$200` further on.
Eight character slots per plate, blanks included, so plate *n* starts at
character *n* × 8.

    シェロオン Sheloon          ダーレス Darles
    魔法の森 Magic Forest       ストーカー城 Stalker Castle
    アリア Aria                 バウバボ Baubabo
    クローグ Kroag              シーバラ Seabara
    ネクストリア Nextria        エルフの角笛 Elf Horn
    魂の塔 Tower of Souls       クロウ Crow
    ゼヴ Zev                    レ・リュース Le Ryus
    魔獣のオアシス Oasis of Beasts   幻想庭園 Phantasm Garden
    いにしえの神殿 Ancient Temple    浮遊要塞 Floating Fortress
    スティール Steel            シュレルの神殿 Temple of Shrell

    python3 tools/plates.py list           the block chain
    python3 tools/plates.py export out/    one PNG per plate

Translating them means redrawing the art and writing a compressor for the format.
The decompressor is done; the compressor is not.

## Monster names

**Text, not art** — but in their own font, not the game's. Done; this is the
record of what the stock code did and what replaced it. The build is
`build/battle_names.py`, the English is on the `Monster names` sheet of the
workbook, and `tools/checknames.py` executes the patched bytes and renders the
result if you want to see it without an emulator.

### What was there

    ROM $152000   LZSS, $2000 -> $7E:4000   the battle font
    ROM $153000   63 entries of 6 bytes, glyph indices, null padded

The font was 128 slots of 16×16 2bpp, four tiles each in **TL TR BL BR** order —
not the arrangement the Japanese font uses, which is why it renders as scrambled
strokes under every other layout. Slots 1-82 held the full katakana set in
gojūon order, ア first; slot 0 and 83-127 blank.

    ORDER = ('アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨ'
             'ワヲラリルレロンャュョッガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポ'
             'ァィゥェォヴー')
    glyph index = 1 + ORDER.index(ch)

So `ワービースト` was `27 52 43 52 0D 14` at `$153018`. Six glyphs was the hard
limit and the Japanese was already truncated by it — `シェルスコ` for Shell
Scorpion.

### The renderer

`$81:F869` draws all six plates. Per monster it reads the name index from
`$0BB5`, multiplies by six, copies the entry into `$084D..$0852`, counts the
non-zero bytes to centre the plate, sets `$084A` (first VRAM cell) and
`$084B`/`$084C` (tile coordinates), and calls `$01:F98F`.

`$01:F98F` runs two loops of six:

    $F99B   per glyph, JSL $01:FA18   DMA the bitmap into VRAM
    $F9D4   per glyph, JSL $01:DD71   write one tilemap entry

`$01:FA18` computes, for cell `c` = `$084A`,

    $0862 = ((c & 7) << 4) + ((c & $F8) << 5)     VRAM word offset
    $0864 = glyph * 64                            source offset in $7E:4000

and fires two DMAs of `$20` bytes: top half to VRAM `$6000+$0862`, bottom half
to `$6080+$0862`.

`$01:DD71` is a generic one-entry tilemap write taking `$0872` = x, `$0874` = y,
`$0876` = the entry. It re-encodes the low byte as `((c & 7) << 1) | ((c & $F8)
<< 2)`.

### Why halving the four constants could not work

**BG3 is in 16×16 character mode.** `$81:E7B9` writes `$79` to `$2105`: mode 1,
and bit 6 set is BG3 char size 16×16. That is the whole explanation for the
shape of the code above — one tilemap entry per glyph, with tile number `2c`,
because the hardware expands entry `t` into tiles `t`, `t+1`, `t+16`, `t+17`,
which is exactly where those two DMAs land. `$0862` stepping by `$10` words per
cell and `$6080` for the bottom half are consequences of the character size, not
free constants.

A tilemap cell is therefore sixteen pixels wide and cannot be made eight.
Halving the DMA sizes and the source stride leaves an eight-pixel bitmap in a
sixteen-pixel cell and never writes the right-hand tile, so whatever the
previous name left in VRAM stays there — that is the "overlapping". Halving
`$0862` as well does not rescue it; it makes consecutive cells write over each
other's tiles.

### What it is now

Keep the 16×16 cell and put **two half-width letters in it**. Cell geometry,
tilemap loop, `$01:DD71`, coordinates and centring are all untouched; only the
source of the four tiles changes. Per cell, four DMAs of `$10` bytes:

    glyph a top    -> VRAM $6000 + $0850        glyph b top    -> $6008 + $0850
    glyph a bottom -> VRAM $6080 + $0850        glyph b bottom -> $6088 + $0850

That gives twelve characters per name in the six cells the layout already has,
and makes the `$2000` block 256 slots of 8×16 — so **the glyph index is just
ASCII** and the name table is plain text.

    ROM $152000   LZSS, still $2000 unpacked, 256 × (8×16, 2bpp)
                  slot n draws chr(n); top tile at n*32, bottom at n*32+$10
    ROM $153000   63 entries of 12 bytes, ASCII, null padded

The glyphs come off `assets/halfwidth_font_sheet.png` like every other font in
the build, with the sheet's shadow dropped — the katakana used colour 3 and
nothing on this BG uses colour 1, so there was no reason to trust a palette
entry nobody has looked at.

Three patches:

    $81:F893   stride 6 -> 12; keep the entry offset in $084D/$084E instead of
               copying six bytes; count cells (the first byte of each pair)
               rather than bytes, so the centring at $F8EC/$F90D still gets 0-6
    $81:F99B   the glyph loop -> JSL PAIRDRAW
    $02:F500   PAIRDRAW, 206 bytes of new code

`$01:FA18` is left in place; `$F9B8` was its only caller. The font recompresses
to 878 bytes against the original 1220, so the block still clears the table at
`$153000` with room to spare.

Twelve characters is the ceiling, because it is still six cells. Wider means the
loop count at `$F9D4` *and* the plate spacing at `$F8EC`/`$F90D`, which is five
columns in the left group and four in the right against a six-cell plate — the
plates only clear each other because alternate slots sit on different rows.

## How they were found

Static searching never would have. What worked:

- **Two savestates that differ in one thing.** Diffing a Sheloon world map
  against a Magic Forest one, and an unpaused battle against a paused one,
  isolated the exact buffers.
- **A trace log, filtered.** `Select-String -Pattern '\\[7e4[a-f]'` over a 46 MB
  bsnes-plus trace found the writes into the staging buffer in one step, and the
  effective address in brackets gave the source: `$2A:A302`, hence the block at
  `$152000`.
- **Switching the tile viewer to 2bpp.** The battle font is invisible at 4bpp.
- **Reading $2105 before believing anything about cell size.** Every wrong
  theory about the nameplate geometry came from inferring it from the drawing
  code instead of from the one register that decides it.

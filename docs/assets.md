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

**Text, not art** — but in their own font, not the game's.

    ROM $152000   LZSS, $2000 -> $7E:4000   the battle font
    ROM $153000   63 entries of 6 bytes, glyph indices, null padded

The font is 128 slots of 16×16 2bpp, four tiles each in **TL TR BL BR** order —
not the arrangement the Japanese font uses, which is why it renders as scrambled
strokes under every other layout. Slots 1-82 hold the full katakana set in gojūon
order, ア first; slot 0 and 83-127 are blank.

    ORDER = ('アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨ'
             'ワヲラリルレロンャュョッガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポ'
             'ァィゥェォヴー')
    glyph index = 1 + ORDER.index(ch)

So `ワービースト` is `27 52 43 52 0D 14`, which appears once in the ROM, at
`$153018`. The full table is dumped in `monster_names.txt`.

Six glyphs is the hard limit and the Japanese is already truncated by it —
`シェルスコ` for Shell Scorpion.

### Making them English

The renderer is `$81:F9D4`. Per glyph it fires two DMAs of `$20` bytes: top half
(TL+TR) to VRAM `$6000`+, bottom half (BL+BR) to `$6080`+, sourced from the font
at `$7E:4000` with `$0864 = index * 64`.

Halving all of that gives 8×16 half-width cells and turns the `$2000` block into
**256 glyph slots instead of 128** — the whole Latin alphabet in both cases plus
digits and punctuation, with no pair encoding needed:

    $FA41  the sixth ASL      index * 64 -> * 32
    $FA74  LDX #$0020         top half, one tile
    $FA98  LDA #$4020         bottom half source base -> $4010
    $FAA9  LDX #$0020         bottom half, one tile

**Tried, and reverted — the glyphs came out overlapping.** The source stride
halves correctly, but the VRAM destination step is computed at `$FA18-$FA44` from
the caller's tile coordinates and still assumes a two-tile-wide cell. That sum has
to halve too, and it is not a constant in the routine: the caller at `$F9DC`
increments `$084A` and `$084B` once per glyph. Trace `$FA18` across two
consecutive glyphs and watch how `$0862` advances.

After that, twelve-character names need the loop count at `$F9D4` (`CPX #$0006`)
widened, which needs the table restriped to 12-byte entries and relocated —
63 × 12 is 756 bytes where 378 fit now — and the table's stride lives inside
`$01:DD71`.

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

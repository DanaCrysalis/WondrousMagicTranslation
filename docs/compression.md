# Compression

The ROM uses two unrelated schemes. RUX holds the intro; a second LZSS holds the
graphics and the battle font, and until late on we only knew about RUX, so every
search for the nameplates came back empty.

## RUX

One compressed archive in the ROM, at `$132000` — 18,149 bytes expanding to
42,382 at `$7F:1DE7`. It holds the intro poem and the prologue text.

Decompressor at `$A6:8B3E`. Format:

    "RUX "                  magic
    uint16                  decompressed size
    uint16                  0
    then groups of:
      uint16 control        MSB first, 16 flags
      flag 0                one literal byte
      flag 1                uint16 w
                            w & $F000 != 0 : length = w >> 12, offset = w & $0FFF
                            w & $F000 == 0 : offset = w & $0FFF, then a byte,
                                             length = byte + $10
                            copy length + 1 bytes from (dest - offset - 1),
                            overlapping

`tools/rux.py` implements both directions. The decompressor was verified against
a savestate: all 42,382 bytes match WRAM exactly. The compressor round-trips and
comes out slightly tighter than the original — 17,927 against 18,149.

    python3 tools/rux.py        # writes data/rux_archive.bin

## Crawl stream format

Inside the archive, the poem and prologue are one continuous stream of 16-bit
words read by `$A6:87DB` through the pointer at `$001B`, initialised to `$1DE7`
at `$A6:8257`.

    word < $20      $0000 ends a section, $0001 ends a record,
                    $0002 steps the cursor back half a cell,
                    $000A ends a row
    word >= $20     glyph, index = word - $20, flat across both font banks
                    (0-191 text, 192-447 kanji)

Rows are two records. `$A6:8799` resets the VRAM address for the first and leaves
it running for the second, and advances the row base by `$200` after the pair —
so **record counts must stay even** or the alternation drifts.

    poem      blob $0000-$07A8
    $0000 marker at $07A8
    prologue  blob $07AA-$0F8C
    $0000 marker at $0F8C

Both sections keep their exact byte length in the English build, so the markers
do not move and nothing after them in the archive shifts.


# The second LZSS

Not RUX, no magic, no relationship to it. Two identical copies of the
decompressor exist: `$90:877A` working through zero page `$30-$38`, and
`$02:D1D9` through `$00-$08`. Battle code calls the second one, so a breakpoint
on the first never fires in battle.

Each block starts with a four-byte header whose first word is the **uncompressed**
size; `$90:8750` adds it to the destination to find the end. The compressed length
is not stored, so blocks can only be walked by decompressing them — but they are
laid end to end, so a chain can be followed from its first block.

    uint16                  uncompressed size
    uint16                  0
    then groups of:
      byte control          MSB first, 8 flags
      each flag consumes one byte first:
        flag 0              that byte is a literal
        flag 1, b < $10     offset = b & $0F
                            copy 2 bytes from (dest - offset - 1)
        flag 1, b >= $10    offset = ((b & $0F) << 8) | next   (12 bits)
                            length = (b >> 4) + 2
                            b >= $F0: length = following byte + 17
                            copy from (dest - offset - 1), overlapping

Long matches are copied by `JSL $00183A`, an `MVN $7e,$7e` trampoline.

`tools/plates.py` implements the decompressor and the chain walk. Verified: block
`$0B3D68` reproduces `$7E:4000-$7E:6800` in a savestate byte for byte.

## Known blocks

| ROM | Unpacked | Destination | What |
|---|---|---|---|
| `$0AF000` | `$2000` | `$7E:4000` | UI icons — buttons, hearts, item icons |
| `$0B3D68` | `$2800` | `$7E:4000` | nameplates 1-10 |
| `$0B4A1E` | `$2800` | `$7E:6800` | nameplates 11-20 |
| `$0B5644` .. `$0BAF90` | `$1800` each | | world map terrain, 7 blocks |
| `$152000` | `$2000` | `$7E:4000` | battle font, 128 × 16×16 katakana |

A ROM-wide scan for the four-byte header is not reliable on its own — a plausible
size with two zero bytes after it matches far too much. Follow chains from a
known block, or get the source address from a breakpoint on the decompressor.

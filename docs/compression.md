# RUX compression

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

# The dialogue text engine

Bank `$90` (mirrored at `$10`, which is what the CPU actually executes). Direct
page is `$1800` — the single most misleading detail in the whole ROM, because a
disassembly labels the variables `$A8`, `$AE` and so on while a debugger needs
`$7E:18A8`, `$7E:18AE`.

## Entry

    JSL $10:9543     A low byte = script bank, X = script offset

`$9543` pushes the bank, does `TXY`, and `PLB`s the bank into `DB`, so the script
pointer becomes `DB:Y`. At the moment the breakpoint fires, `DB` and `Y` still
hold the caller's values — read `A` and `X` instead.

`$9859` fetches one byte: `LDA $0000,Y / INY`, and on a `Y` wrap increments `DB`
and reloads `Y = $8000`, so strings cross LoROM bank boundaries correctly.

## Control codes

| Byte | Handler | Args | Meaning |
|---|---|---:|---|
| `$00` | — | 0 | **end of string** |
| `$01` | `$95BD` | 0 | no-op |
| `$02` | `$9751` | 2 | print name via the `$7E:3208` pointer table |
| `$03` | `$978B` | 2 | 7-digit decimal |
| `$04` | `$9787` | 2 | 8-digit decimal |
| `$05` | `$96B5` | 0 | flush and wait for input |
| `$06` | `$96E1` | 1 | `JSL $10:94F1` |
| `$07` | `$970A` | 4 | `JSL $10:94E7` |
| `$08` | `$97FB` | 1 | indirect call via `$7E:3208` |
| `$09` | `$9738` | 2 | `JSL $10:94EB` |
| `$0A` | `$96D2` | 0 | new page / clear |
| `$0B` | `$96EB` | 1 | sound effect |
| `$0C` | `$96F5` | 1 | `JSL $00:FB7C`; arg 3 → `JSL $10:D7AD` |
| `$0D` | `$96BE` | 0 | **newline** |
| `$0E-$1D` | — | 0 | unhandled, exits like `$00` |
| `$1E` | — | 1 | kanji glyph, index = argument |
| `$1F` | — | 1 | UI glyph, index = arg & `$7F`, X-flip on bit 7 |
| `$20-$DF` | — | 0 | text glyph, index = byte − `$20` |
| `$E0-$FF` | table `$081675` | 0 | window frame, fixed glyph plus flips |

Dispatch is a `CMP` chain in non-numeric order, so pairing the jump table with
codes in sequence gets the handlers wrong. `$00` is the terminator — it falls
through every comparison and reaches `PLB / RTL`.

## Cell descriptor buffer

`$7E:2C00`, 16 columns × 16 rows of words. `$9841` computes the index as
`(row & 15) * 32 + (col & 15) * 2`. Row 15 doubles as `$2DE0`, the staging row
DMA'd to the tilemap, so rows 0–14 are usable. `$AE` is the column, `$AF` the row,
`$B4` the left margin, `$B5`/`$B7` the row limits.

A dialogue box occupies rows 9–14 with the frame in columns 0 and 15, leaving 14
text cells.

### Stock descriptor

    tile = (c >> 3) * 32 + (c & 7) * 2 + (flags & $11)
    attr = (($AD | (flags & $C0)) ^ $20)

`c` is the glyph index and `flags` the low byte — `$01` text bank, `$10` kanji
bank, `$00` a static frame tile already in VRAM. Bits 6-7 are H/V flip.

### VRAM is a per-cell cache, not a font sheet

`$9AA0` builds the tilemap word from **screen position only**:

    tile = $0200 + row' * 64 + (col >= 8 ? $20 : 0) + (col & 7) * 2
    attr = descriptor & $FC00          ; always $2C00 for text

where `row'` is `row`, or `row - 5` for rows ≥ 6. The character code never
reaches the tilemap; it only selects the ROM source in `$9A67`. That is why every
VRAM dump looks like a composed screen rather than a font.

## Half-width patch

Because the tilemap is position-derived, two half-width glyphs can share a cell
with no change to the tilemap, the scroll or the buffer size.

    bit 0        1 = text cell
    bits 1-7     left glyph index  (1-96)
    bits 8-9     right glyph index, bits 0-1
    bit 10       left alone - the menu cursor EORs this to highlight a row
    bits 11-15   right glyph index, bits 2-6

A right index of 0 means the right half is unwritten, so no separate flag is
needed. Bit 10 has to stay clear of the index: the menu highlight flips it on
every cell of the selected row, and with a contiguous index there it shifted
every second letter by four. `$9ACB` carries that bit into the tilemap attribute
as palette bit 0, which is what it meant originally, so the highlight still
changes colour.

Parity needs no variable: a cell with bit 0 set and bit 15 clear is waiting for
its right half. Glyph `h` draws ASCII `h + $1F`, so script bytes `$20-$7E` are
literally ASCII, and `$7F` is a dedicated half-width space (glyph 96, blank).
`$20` stays a full-width static cell — the window frames and menu padding count
it as a whole cell.

Patch sites are in `docs/memory-map.md`. Two of them exist only because of
mistakes worth remembering:

- **`$95CB`** — byte `$20` branches off at `$95C8` and emits flags `$00`, which
  routes to the static path and stamps a blank over a half-open cell. That ate
  the character before every space.
- **`$96CC`** — the newline hook may only clear a *stale half-open text cell*.
  `$96BE` advances `$AF` before calling it, so on the last text line the cursor
  is standing on the border row, and an unconditional clear wipes a frame cell.

## Script pointers

Block C strings are reached through stubs at `$90:920C` onward, each
`LDA #$12 / LDX #offset`. Block B is addressed some other way — there is no
`LDA #$13` anywhere in the ROM — so relocating story strings is still an open
problem, and translations have to fit their original byte length.

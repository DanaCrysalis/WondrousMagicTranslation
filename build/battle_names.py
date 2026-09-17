#!/usr/bin/env python3
"""Monster names in battle, in English.

The names are not script. They are glyph indices into a katakana font that
nothing else uses, drawn by a routine of their own. `docs/assets.md` has the
trail; this is the conversion.

What the stock code does
------------------------

$81:F869 draws all six nameplates. Per monster it reads the name index out of
$0BB5, multiplies by six, copies six bytes from $2A:B000 ($153000) into
$084D..$0852, counts the non-zero ones to centre the plate, and calls
$01:F98F with $084A = first VRAM cell, $084B/$084C = tile coordinates.

$01:F98F does two passes of six:

    $F99B   per glyph, JSL $01:FA18 - DMA the bitmap into VRAM
    $F9D4   per glyph, JSL $01:DD71 - write one tilemap entry

$01:FA18 computes, for cell c = $084A,

    $0862 = ((c & 7) << 4) + ((c & $F8) << 5)     VRAM word offset
    $0864 = glyph * 64                            source offset in $7E:4000

and fires two DMAs of $20 bytes: $7E:4000+$0864 to VRAM $6000+$0862, and
$7E:4020+$0864 to $6080+$0862.

Why halving the four constants could not work
---------------------------------------------

**BG3 is in 16x16 character mode.** $81:E7B9 writes $79 to $2105: mode 1, and
bit 6 set is BG3 char size 16x16. That is why $01:DD71 writes *one* tilemap
entry per glyph, with tile number ((c & 7) << 1) | ((c & $F8) << 2) - the
hardware expands entry t into tiles t, t+1, t+16, t+17, which is exactly where
the two DMAs put the four tiles. $0862 stepping by $10 words per cell and $6080
for the bottom half are both consequences of that, not free constants.

A tilemap cell is therefore 16 pixels wide and cannot be made 8. Halving the
DMA sizes and the source stride leaves an 8-pixel bitmap in a 16-pixel cell with
the right-hand tile never written - whatever was in VRAM from the previous name
stays there, which is the reported "overlapping". Halving $0862 as well does not
fix it; it makes consecutive cells write over each other's tiles instead.

What this does instead
----------------------

Keep the 16x16 cell and put **two half-width letters in it**. The cell geometry,
the tilemap loop, $01:DD71, the coordinates and the centring are all untouched.
Only the source of the four tiles changes: instead of one glyph's TL TR BL BR,
a cell takes the top and bottom tiles of glyph *a* on the left and of glyph *b*
on the right, four DMAs of $10 bytes.

That gives twelve characters per name in the six cells the layout already has,
and turns the $2000 font block into 256 slots of 8x16 - so the glyph index is
just ASCII, and the name table is plain text.

    $152000   LZSS block, still $2000 unpacked, now 256 x (8x16, 2bpp)
              slot n draws chr(n); top tile at n*32, bottom at n*32+$10
    $153000   63 entries of 12 bytes, ASCII, null padded

Patches
-------

    $81:F893   stride 6 -> 12; keep the entry offset in $084D; count cells
               (the first byte of each pair) instead of bytes
    $81:F99B   the glyph loop -> JSL PAIRDRAW
    $02:F500   PAIRDRAW, new code

$01:FA18 is left in place. $F9B8 was its only caller.

Still six cells, so twelve characters is the ceiling. Going wider means both the
loop count at $F9D4 and the plate spacing at $F8EC/$F90D, which is 5 columns in
the left group and 4 in the right against a 6-cell plate - the plates only clear
each other because alternate slots sit on different rows.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
import glyphs
import lzss

FONT_BLOCK = 0x152000            # LZSS, $2000 to $7E:4000
FONT_LIMIT = 0x153000            # the name table starts here
TABLE = 0x153000                 # $2A:B000
TABLE_END = 0x1533FF             # filler beyond this point
ENTRIES = 63
WIDTH = 12                       # bytes per entry = characters per name
CELLS = 6                        # 16x16 tilemap cells per plate

CODE = 0x017500                  # $02:F500, free to the end of the bank
CODE_ORG = 0xF500
CODE_BANK = 0x02

ORDER = ('アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨ'
         'ワヲラリルレロンャュョッガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポ'
         'ァィゥェォヴー')


def japanese(rom):
    """The stock names, decoded off the 6-byte table. For the workbook."""
    out = []
    for i in range(ENTRIES):
        e = rom[TABLE + i * 6:TABLE + i * 6 + 6]
        out.append(''.join(ORDER[b - 1] for b in e if b))
    return out


# ---------------------------------------------------------------- the font --

def font():
    """256 slots of 8x16, 2bpp, top tile then bottom. Slot n draws chr(n)."""
    buf = bytearray(256 * 32)
    for n in range(0x20, 0x7F):
        px = glyphs.half(chr(n))
        o = n * 32
        for part in (0, 1):
            for y in range(8):
                p0 = p1 = 0
                for x in range(8):
                    # the katakana used colour 3 only and nothing else on this
                    # BG uses colour 1, so the sheet's shadow is dropped rather
                    # than drawn in a palette entry nobody has looked at
                    v = 3 if px[part * 8 + y][x] == 3 else 0
                    p0 |= (v & 1) << (7 - x)
                    p1 |= ((v >> 1) & 1) << (7 - x)
                buf[o + part * 16 + y * 2] = p0
                buf[o + part * 16 + y * 2 + 1] = p1
    return bytes(buf)


# ----------------------------------------------------------------- the code --

def _code():
    """PAIRDRAW: draw one six-cell plate as twelve half-width letters."""
    out = bytearray()
    labels, fixups = {}, []

    def emit(*bs):
        out.extend(bs)

    def label(n):
        labels[n] = CODE_ORG + len(out)

    def abs_at(n):
        fixups.append((len(out), n)); emit(0, 0)

    # -- PAIRDRAW --------------------------------------------------------
    # entry: $084A = first cell, $084D/$084E = offset of the entry in the table.
    # M is 8-bit and X/Y 16-bit on the way in; PHP/PLP hands that back.
    label('PAIRDRAW')
    emit(0x08)                          # PHP
    emit(0x8B)                          # PHB
    emit(0xE2, 0x20)                    # SEP #$20
    emit(0xA9, 0x00)                    # LDA #$00
    emit(0x48)                          # PHA
    emit(0xAB)                          # PLB            DB = 0: WRAM and I/O
    emit(0xC2, 0x30)                    # REP #$30
    emit(0xAD, 0x4D, 0x08)              # LDA $084D
    emit(0xAA)                          # TAX            X walks the entry
    emit(0xE2, 0x20)                    # SEP #$20
    emit(0x9C, 0x4F, 0x08)              # STZ $084F      cell counter

    label('CELL')
    # ---- VRAM word offset for cell c = $084A + i, the sum $01:FA18 computes
    emit(0xAD, 0x4A, 0x08)              # LDA $084A
    emit(0x18)                          # CLC
    emit(0x6D, 0x4F, 0x08)              # ADC $084F
    emit(0xC2, 0x20)                    # REP #$20
    emit(0x29, 0xFF, 0x00)              # AND #$00FF     c
    emit(0x48)                          # PHA
    emit(0x29, 0x07, 0x00)              # AND #$0007
    emit(0x0A, 0x0A, 0x0A, 0x0A)        # ASL x4         (c & 7) << 4
    emit(0x48)                          # PHA
    emit(0xA3, 0x03)                    # LDA $03,S      c
    emit(0x29, 0xF8, 0x00)              # AND #$00F8
    emit(0x0A, 0x0A, 0x0A, 0x0A, 0x0A)  # ASL x5         (c & $F8) << 5
    emit(0x18)                          # CLC
    emit(0x63, 0x01)                    # ADC $01,S
    emit(0x8D, 0x50, 0x08)              # STA $0850      VRAM word offset
    emit(0x68)                          # PLA
    emit(0x68)                          # PLA

    for base_top, base_bot in ((0x6000, 0x6080), (0x6008, 0x6088)):
        # ---- one half-width glyph: top tile left/right, bottom tile left/right
        emit(0xE2, 0x20)                # SEP #$20
        emit(0xBF, 0x00, 0xB0, 0x2A)    # LDA $2AB000,X  the letter, = ASCII
        emit(0xC2, 0x20)                # REP #$20
        emit(0x29, 0xFF, 0x00)          # AND #$00FF
        emit(0x0A, 0x0A, 0x0A, 0x0A, 0x0A)   # ASL x5    slot * 32
        emit(0x18)                      # CLC
        emit(0x69, 0x00, 0x40)          # ADC #$4000     top tile in the block
        emit(0xA8)                      # TAY
        emit(0xA9, base_top & 0xFF, base_top >> 8)
        emit(0x20); abs_at('PUT')       # JSR PUT
        emit(0x98)                      # TYA
        emit(0x18)                      # CLC
        emit(0x69, 0x10, 0x00)          # ADC #$0010     bottom tile
        emit(0xA8)                      # TAY
        emit(0xA9, base_bot & 0xFF, base_bot >> 8)
        emit(0x20); abs_at('PUT')       # JSR PUT
        emit(0xE8)                      # INX

    emit(0xE2, 0x20)                    # SEP #$20
    emit(0xEE, 0x4F, 0x08)              # INC $084F
    emit(0xAD, 0x4F, 0x08)              # LDA $084F
    emit(0xC9, CELLS)                   # CMP #$06
    emit(0xF0, 0x03)                    # BEQ +3
    emit(0x4C); abs_at('CELL')          # JMP CELL
    emit(0xAB)                          # PLB
    emit(0x28)                          # PLP
    emit(0x6B)                          # RTL

    # -- PUT -------------------------------------------------------------
    # A = VRAM base for this tile, Y = byte offset of the tile in $7E:4000.
    # Entered and left with M 16-bit; the 8-bit stretch in the middle is local.
    # One 2bpp tile is $10 bytes; VRAM addresses here are word addresses, so
    # the DMA advances $2116 by 8 and the four tiles of a cell land at
    # +0, +8, +$80, +$88 - which is tiles t, t+1, t+16, t+17 of the 16x16
    # character the tilemap entry names.
    label('PUT')
    emit(0x18)                          # CLC
    emit(0x6D, 0x50, 0x08)              # ADC $0850
    emit(0x8D, 0x16, 0x21)              # STA $2116      16-bit: $2116/$2117
    emit(0xE2, 0x20)                    # SEP #$20
    emit(0xA9, 0x01)                    # LDA #$01       2 registers, $2118/9
    emit(0x8D, 0x40, 0x43)              # STA $4340
    emit(0xA9, 0x18)                    # LDA #$18
    emit(0x8D, 0x41, 0x43)              # STA $4341
    emit(0xC2, 0x20)                    # REP #$20
    emit(0x98)                          # TYA
    emit(0x8D, 0x42, 0x43)              # STA $4342
    emit(0xE2, 0x20)                    # SEP #$20
    emit(0xA9, 0x7E)                    # LDA #$7E
    emit(0x8D, 0x44, 0x43)              # STA $4344
    emit(0xC2, 0x20)                    # REP #$20
    emit(0xA9, 0x10, 0x00)              # LDA #$0010
    emit(0x8D, 0x45, 0x43)              # STA $4345
    emit(0xE2, 0x20)                    # SEP #$20
    emit(0xA9, 0x10)                    # LDA #$10       channel 4
    emit(0x8D, 0x0B, 0x42)              # STA $420B
    emit(0xC2, 0x20)                    # REP #$20       hand M back 16-bit:
    emit(0x60)                          # RTS            every caller resumes
                                        #                with a 16-bit immediate

    for off, name in fixups:
        v = labels[name]
        out[off], out[off + 1] = v & 0xFF, v >> 8
    return bytes(out), labels


# ------------------------------------------------------------------ apply ---

def _patch(rom, off, data, expect):
    got = bytes(rom[off:off + len(expect)])
    assert got == bytes(expect), 'unexpected bytes at $%06X: %s' % (off, got.hex())
    rom[off:off + len(data)] = data


def apply(rom, names):
    """names: 63 strings of at most 12 ASCII characters."""
    assert len(names) == ENTRIES, 'want %d names, got %d' % (ENTRIES, len(names))

    # -- the name table: 12-byte ASCII entries, in place ------------------
    old = bytes(rom[TABLE:TABLE + ENTRIES * 6])
    assert old[:6] == bytes([0x42, 0x32, 0x14, 0, 0, 0]), 'not the stock name table'
    table = bytearray()
    for i, n in enumerate(names):
        assert len(n) <= WIDTH, '%r is %d characters, %d is the limit' % (n, len(n), WIDTH)
        assert all(0x20 <= ord(c) < 0x7F for c in n), 'non-ASCII in %r' % n
        table += n.encode('ascii').ljust(WIDTH, b'\x00')
    end = TABLE + len(table)
    assert end <= TABLE_END, 'name table runs past $%06X' % TABLE_END
    assert all(b in (0x00, 0xFF) for b in rom[TABLE + ENTRIES * 6:end]), 'table space not free'
    rom[TABLE:end] = table

    # -- the font block ---------------------------------------------------
    was = lzss.block(rom, FONT_BLOCK)[1] - FONT_BLOCK
    raw = font()
    enc = lzss.compress(raw)
    assert lzss.decompress(enc, 4, len(raw))[0] == raw, 'font does not round-trip'
    room = FONT_LIMIT - FONT_BLOCK
    assert len(enc) <= room, 'font block is %d bytes, %d fit' % (len(enc), room)
    rom[FONT_BLOCK:FONT_BLOCK + room] = enc + b'\xff' * (room - len(enc))

    # -- new code ---------------------------------------------------------
    code, labels = _code()
    assert all(b == 0xFF for b in rom[CODE:CODE + len(code)]), 'code space not free'
    rom[CODE:CODE + len(code)] = code

    # -- $81:F893  stride 6 -> 12, and count cells rather than bytes ------
    # X comes in holding n; 12*(n-1) is the same shape as 6*(n-1) with one more
    # ASL. The offset is kept in $084D/$084E instead of the six bytes being
    # copied, and the cell count walks the entry two bytes at a time, so the
    # centring at $F8EC/$F90D still gets 0-6 and does not change.
    new = bytes([
        0x3A,                          # DEC          n - 1
        0x0A,                          # ASL          x2
        0x0A,                          # ASL          x4   (clears carry)
        0x48,                          # PHA
        0x0A,                          # ASL          x8
        0x63, 0x01,                    # ADC $01,S    x12
        0xAA,                          # TAX
        0x68,                          # PLA
        0x8E, 0x4D, 0x08,              # STX $084D    entry offset
        0xE2, 0x20,                    # SEP #$20
        0x5A,                          # PHY
        0xA0, 0x00, 0x00,              # LDY #$0000   cells used
        0xBF, 0x00, 0xB0, 0x2A,        # LDA $2AB000,X   left letter of a cell
        0xF0, 0x08,                    # BEQ +8
        0xE8, 0xE8,                    # INX INX
        0xC8,                          # INY
        0xC0, 0x06, 0x00,              # CPY #$0006
        0xD0, 0xF2,                    # BNE -14
        0x98,                          # TYA
        0x7A,                          # PLY
        0x4A,                          # LSR          half the width, to centre
        0x48,                          # PHA
        0x4C, 0xE1, 0xF8,              # JMP $F8E1
    ])
    old_head = bytes(rom[0x00F893:0x00F8E1])
    assert old_head[:10] == bytes([0x3A, 0x0A, 0x48, 0x0A, 0x63, 0x01, 0xAA, 0x68, 0xE2, 0x20])
    _patch(rom, 0x00F893, new + b'\xea' * (0x4E - len(new)), old_head)

    # -- $81:F99B  the glyph loop -> PAIRDRAW ------------------------------
    # $F99B-$F9C3 is the six-glyph DMA loop and nothing else jumps into it;
    # $F9C4 onwards restores $084A/$084B and runs the tilemap loop unchanged.
    j = labels['PAIRDRAW']
    _patch(rom, 0x00F99B,
           bytes([0x22, j & 0xFF, j >> 8, CODE_BANK,   # JSL PAIRDRAW
                  0x4C, 0xC4, 0xF9]) + b'\xea' * 34,   # JMP $F9C4
           bytes.fromhex('a20000e0060030034cc4f9dac220a301aabd4d08'
                         '29ff00e220ebad4a082218fa01ee4a08fae84c9ef9'))
    assert rom[0x00F9C4] == 0x68, 'clobbered past the loop'

    return len(enc), was, len(code)


if __name__ == '__main__':
    rom = paths.rom()
    for i, jp in enumerate(japanese(rom)):
        print('%2d  %s' % (i, jp))

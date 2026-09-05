#!/usr/bin/env python3
"""Wondrous Magic - half-width text patch.

Cell descriptor after this patch (word at $7E:2C00 + row*32 + col*2):

    bit 0        1 = text cell   (kept, $90:99F9 tests it)
    bits 1-7     left  glyph index h   (1-96, 0 = empty)
    bits 8-9     right glyph index, bits 0-1
    bit 10       LEFT ALONE - the menu cursor EORs this bit to highlight a row
    bits 11-15   right glyph index, bits 2-6

Bit 10 is why the right index is split. The menu highlight flips it on every cell
of the selected row; with a contiguous index there it shifted every second letter
by four. Nothing reads it now, so the flip is harmless.

A right index of 0 means the right half has not been written yet - h = 0 is the
reserved empty glyph and an explicit space is h = 96 - so no separate flag is
needed.

Parity needs no variable: a cell with bit0 set and bit15 clear is waiting for its
right half. $18B9 turned out to be used by the battle target cursor, so nothing in
direct page is borrowed.

Glyph h lives at $15:8000 + h*32 (16 bytes top tile, then 16 bytes bottom tile) and
draws ASCII code h + $1F, so script bytes $20-$7E are literally ASCII.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths

import sys

ROM = bytearray(open(paths.ROM_IN,'rb').read())
BASE = 0x086900          # ROM offset of free space
ORG = 0xE900             # $90:E900

code = bytearray()
labels, fixups = {'LOOP': 0x957C}, []

def emit(*bs): code.extend(bs)
def label(n): labels[n] = ORG + len(code)
def word_at(n, addend=0):
    fixups.append((len(code), n, addend, 'abs')); emit(0, 0)
def rel_at(n):
    fixups.append((len(code), n, 0, 'rel')); emit(0)
def rel16_at(n):
    fixups.append((len(code), n, 0, 'rel16')); emit(0, 0)

# ---------------------------------------------------------------- renderer --
# hook replaces $9608 "PHA / AND #$11" with "JMP RENDER"
label('RENDER')
emit(0x48)                       # PHA            save flags
emit(0x29, 0x11)                 # AND #$11
emit(0xD0); rel_at('HALF')       # BNE HALF
# static-tile cell (window frame, $1F icon, full-width space $20).
# If the current cell is half-open, close it and step on, so the static write
# lands on a fresh cell instead of erasing the character sitting there.
emit(0xC2, 0x20)                 # REP #$20
emit(0x48)                       # PHA            keep B = c across the 16-bit load
emit(0xBF, 0x00, 0x2C, 0x7E)     # LDA $7E2C00,X
emit(0x89, 0x01, 0x00)           # BIT #$0001
emit(0xF0); rel_at('ST')         # BEQ ST
emit(0x89, 0x00, 0xFB)           # BIT #$FB00     right index, ignoring bit 10
emit(0xD0); rel_at('ST')         # BNE ST
emit(0x09, 0x00, 0xC0)           # ORA #$C000     close it with a blank (h = 96)
emit(0x9F, 0x00, 0x2C, 0x7E)     # STA $7E2C00,X
emit(0xE2, 0x20)                 # SEP #$20
emit(0xE6, 0xAE)                 # INC $AE
emit(0xE8, 0xE8)                 # INX INX
emit(0xC2, 0x20)                 # REP #$20
label('ST')
emit(0x68)                       # PLA            A = flags & $11, B = c again
emit(0xE2, 0x20)                 # SEP #$20
emit(0x4C, 0x0B, 0x96)           # JMP $960B
label('HALF')
emit(0x68)                       # PLA
emit(0xEB)                       # XBA            A = c
emit(0x1A)                       # INC A          A = h = c + 1
emit(0xC2, 0x20)                 # REP #$20
emit(0x29, 0xFF, 0x00)           # AND #$00FF
emit(0x85, 0xA8)                 # STA $A8        $A8 = h
emit(0xBF, 0x00, 0x2C, 0x7E)     # LDA $7E2C00,X
emit(0x89, 0x01, 0x00)           # BIT #$0001     text cell already open?
emit(0xF0); rel_at('NEWCELL')    # BEQ -> NEWCELL
emit(0x89, 0x00, 0xFB)           # BIT #$FB00     right half already used?
emit(0xD0); rel_at('NEWCELL')    # BNE -> NEWCELL
# fill the right half: index bits 0-1 at 8-9, bits 2-6 at 11-15, skipping bit 10
emit(0x48)                       # PHA            save current word
emit(0xA5, 0xA8)                 # LDA $A8
emit(0x29, 0x03, 0x00)           # AND #$0003
emit(0xEB)                       # XBA            (h & 3) << 8
emit(0x48)                       # PHA
emit(0xA5, 0xA8)                 # LDA $A8
emit(0x29, 0x7C, 0x00)           # AND #$007C
emit(0x0A)                       # ASL A
emit(0xEB)                       # XBA            (h & $7C) << 9
emit(0x03, 0x01)                 # ORA $01,S
emit(0x03, 0x03)                 # ORA $03,S
emit(0x9F, 0x00, 0x2C, 0x7E)     # STA $7E2C00,X
emit(0x68)                       # PLA
emit(0x68)                       # PLA
emit(0xE2, 0x20)                 # SEP #$20
emit(0x4C, 0x31, 0x96)           # JMP $9631      advance cell, run original tail
label('NEWCELL')
emit(0xA5, 0xA8)                 # LDA $A8
emit(0x0A)                       # ASL A          h << 1
emit(0x09, 0x01, 0x00)           # ORA #$0001     mark as text cell
emit(0x9F, 0x00, 0x2C, 0x7E)     # STA $7E2C00,X
emit(0xE2, 0x20)                 # SEP #$20
emit(0xE6, 0xAA)                 # INC $AA        row is dirty
emit(0x60)                       # RTS            cursor does not advance

# ----------------------------------------------------------------- newline --
# hook replaces "JSR $9841" at $96CC
label('NEWNL')
# This used to recompute X for the NEW row first and then clear the cell there,
# which meant it never touched the half-open cell it was leaving behind - that
# cell is on the row we are moving off. Close the old one, then recompute.
#
# Close, not clear: the character sitting in the left half is real text. Cure
# Herb is nine letters, so its last cell is half open, and clearing it would
# take the b off the description. Filling the right half with a blank leaves the
# b visible and makes the cell complete, so whatever draws next overwrites it
# instead of moving into its free half.
emit(0x20); word_at('CELL')      # JSR CELL       close the cell we are leaving
emit(0x4C, 0x41, 0x98)           # JMP $9841      recompute X for the new row

# ------------------------------------------------------------ name padding --
# $9751 pads the name field to a whole number of cells: pad = arg + old $AE - new $AE.
# A name that ends mid-cell leaves $AE one short, the pad comes out one too large, and
# $965D blanks the cell the name is sitting in. Close any open cell before the count.
label('NEWARG')
emit(0xC2, 0x20)                 # REP #$20
emit(0x48)                       # PHA
emit(0xBF, 0x00, 0x2C, 0x7E)     # LDA $7E2C00,X
emit(0x89, 0x01, 0x00)           # BIT #$0001
emit(0xF0); rel_at('ARGDONE')    # BEQ ARGDONE
emit(0x89, 0x00, 0xFB)           # BIT #$FB00
emit(0xD0); rel_at('ARGDONE')    # BNE ARGDONE
emit(0x09, 0x00, 0xC0)           # ORA #$C000
emit(0x9F, 0x00, 0x2C, 0x7E)     # STA $7E2C00,X
emit(0xE2, 0x20)                 # SEP #$20
emit(0xE6, 0xAE)                 # INC $AE
emit(0xE8, 0xE8)                 # INX INX
emit(0xC2, 0x20)                 # REP #$20
label('ARGDONE')
emit(0x68)                       # PLA
emit(0xE2, 0x20)                 # SEP #$20
emit(0x4C, 0x59, 0x98)           # JMP $9859   read the width byte and return

# ------------------------------------------------------------- highlight ----
# The tilemap attribute has to be a constant now, because the descriptor's high
# bits carry glyph data. Bit 10 is the exception: the menu cursor EORs it, and in
# the stock scheme that was palette bit 0. Carry it through so the selected row
# still changes colour.
label('HIATTR')
emit(0xBD, 0x00, 0x2C)           # LDA $2C00,X    descriptor
emit(0x29, 0x00, 0x04)           # AND #$0400     the cursor's bit
# $2C00 already had bit 10 set, so it swallowed the bit we had just masked out
# and every row came out palette 3 - the highlight stopped changing colour.
# Palette 2 plus priority is $2800, and bit 10 arrives from the descriptor.
#
# The menu leaves bit 10 set on the rows it is NOT on and clears it on the one
# it is, so the bit has to be flipped or the highlight lands on every row but
# the selected one.
emit(0x49, 0x00, 0x04)           # EOR #$0400     selected row, not the others
emit(0x09, 0x00, 0x28)           # ORA #$2800     palette 2 / priority
emit(0x05, 0xA8)                 # ORA $A8        tile from the position math
emit(0x60)                       # RTS

# ------------------------------------------------------------- close cell --
# A field that ends on a half-open cell used to survive into the next screen.
# The stale cell still has bit 0 set and no right half, so the first half-width
# character of whatever drew next was taken as its RIGHT half - the old digit
# stayed put on the left and everything after it shifted by half a cell. That is
# the status screen leaking into the main menu.
#
# Both the cursor move ($09) and the window setup ($07) close the current cell
# first, so a screen can never hand a half-open one to its successor. Same
# blank-h-96 fill the static path already uses.
label('CELL')                    # close a half-open cell, nothing else
emit(0xC2, 0x20)                 # REP #$20
emit(0xBF, 0x00, 0x2C, 0x7E)     # LDA $7E2C00,X
emit(0x89, 0x01, 0x00)           # BIT #$0001     a text cell at all?
emit(0xF0); rel_at('CLDONE')     # BEQ CLDONE
emit(0x89, 0x00, 0xFB)           # BIT #$FB00     right half already used?
emit(0xD0); rel_at('CLDONE')     # BNE CLDONE
emit(0x09, 0x00, 0xC0)           # ORA #$C000     close it with a blank
emit(0x9F, 0x00, 0x2C, 0x7E)     # STA $7E2C00,X
emit(0xE6, 0xAA)                 # INC $AA        row is dirty - $9631 does this
                                 # on every ordinary advance, and without it the
                                 # descriptor changes but the tilemap does not
label('CLDONE')
emit(0xE2, 0x20)                 # SEP #$20
emit(0x60)                       # RTS

label('CLOSE')                   # for the $07 and $09 handlers
emit(0x20); word_at('CELL')      # JSR CELL
emit(0x4C, 0x6A, 0x98)           # JMP $986A      what both handlers did first

# --------------------------------------------------------------- dictionary --
# $1E used to be the kanji escape. With the script in ASCII the kanji bank is
# dead, so $1E nn is repurposed as a dictionary reference: entry nn is printed
# by re-entering the interpreter at $954F, exactly the way $02 prints a name.
# Two bytes for a whole word - without it English does not fit its budgets,
# because Japanese kana carry far more meaning per byte.
label('DICT')
emit(0x20, 0x59, 0x98)           # JSR $9859      entry index
emit(0xC9, 0xFF)                 # CMP #$FF       $FF and $FE escape to the
emit(0xF0); rel_at('DICT2')      # BEQ DICT2      second and third banks
emit(0xC9, 0xFE)                 # CMP #$FE
emit(0xF0); rel_at('DICT3')      # BEQ DICT3
emit(0x8B)                       # PHB
emit(0x5A)                       # PHY            save the outer script pointer
emit(0xC2, 0x30)                 # REP #$30
emit(0x29, 0xFF, 0x00)           # AND #$00FF
emit(0x80); rel_at('DCOMMON')    # BRA DCOMMON
label('DICT3')
emit(0x20, 0x59, 0x98)           # JSR $9859      low byte of a 512+ index
emit(0x8B)                       # PHB
emit(0x5A)                       # PHY
emit(0xC2, 0x30)                 # REP #$30
emit(0x29, 0xFF, 0x00)           # AND #$00FF
emit(0x18)                       # CLC
emit(0x69, 0x00, 0x02)           # ADC #$0200
emit(0x80); rel_at('DCOMMON')    # BRA DCOMMON
label('DICT2')
emit(0x20, 0x59, 0x98)           # JSR $9859      low byte of a 256+ index
emit(0x8B)                       # PHB
emit(0x5A)                       # PHY
emit(0xC2, 0x30)                 # REP #$30
emit(0x29, 0xFF, 0x00)           # AND #$00FF
emit(0x18)                       # CLC
emit(0x69, 0x00, 0x01)           # ADC #$0100
label('DCOMMON')
emit(0x0A)                       # ASL A
emit(0xAA)                       # TAX
emit(0xBF, 0x00, 0xA0, 0x3E)     # LDA $3EA000,X  pointer table
emit(0xAA)                       # TAX
emit(0xE2, 0x20)                 # SEP #$20
emit(0xA9, 0x3E)                 # LDA #$3E       dictionary bank
emit(0xE6, 0xAB)                 # INC $AB        mark nested: suppress the flush
emit(0x22, 0x4F, 0x95, 0x10)     # JSL $10:954F
emit(0xC6, 0xAB)                 # DEC $AB
emit(0xC2, 0x30)                 # REP #$30
emit(0x7A)                       # PLY
emit(0xAB)                       # PLB
emit(0xE2, 0x20)                 # SEP #$20
emit(0x82); rel16_at('LOOP')     # BRL $957C

# ---------------------------------------------------------------- uploader --
# hook replaces $9A6B onward
label('NEWUP')
emit(0xBD, 0x00, 0x2C)           # LDA $2C00,X    descriptor
emit(0x85, 0xA8)                 # STA $A8
emit(0x98)                       # TYA            Y = col*2
emit(0x0A, 0x0A, 0x0A, 0x0A)     # ASL x4         col*32
emit(0xE2, 0x20)                 # SEP #$20
emit(0xEB)                       # XBA
emit(0x0A)                       # ASL A          +$100 once col >= 8
emit(0xEB)                       # XBA
emit(0xC2, 0x20)                 # REP #$20
emit(0xA8)                       # TAY            Y = staging offset
emit(0xA5, 0xA8)                 # LDA $A8
emit(0x29, 0xFE, 0x00)           # AND #$00FE     left h << 1
emit(0x0A, 0x0A, 0x0A, 0x0A)     # ASL x4         h * 32
emit(0xAA)                       # TAX
emit(0x20); word_at('COPYCELL')  # JSR COPYCELL
emit(0xA5, 0xA8)                 # LDA $A8        right index, reassembled
emit(0xEB)                       # XBA
emit(0x29, 0x03, 0x00)           # AND #$0003     bits 0-1 from descriptor 8-9
emit(0x48)                       # PHA
emit(0xA5, 0xA8)                 # LDA $A8
emit(0x4A)                       # LSR A
emit(0xEB)                       # XBA            >> 9
emit(0x29, 0x7C, 0x00)           # AND #$007C     bits 2-6 from descriptor 11-15
emit(0x03, 0x01)                 # ORA $01,S
emit(0x0A, 0x0A, 0x0A, 0x0A, 0x0A)  # ASL x5      h * 32
emit(0xAA)                       # TAX
emit(0x68)                       # PLA
emit(0x98)                       # TYA
emit(0x18)                       # CLC
emit(0x69, 0x10, 0x00)           # ADC #$0010     right-hand tile of the cell
emit(0xA8)                       # TAY
emit(0x20); word_at('COPYCELL')  # JSR COPYCELL
emit(0x4C, 0xA0, 0x9A)           # JMP $9AA0      position -> tilemap word

label('COPYCELL')                # X = font offset, Y = staging offset
# The half-width font lives at $3E:9000, NOT at $15:8000. The Japanese font has
# to stay where it is: the title screen and name entry read it directly and are
# not part of this text engine.
for i in range(8):               # top tile  -> $2E00,Y
    emit(0xBF, 0x00 + i*2, 0x90, 0x3E)
    emit(0x99, 0x00 + i*2, 0x2E)
for i in range(8):               # bottom tile -> $2F00,Y
    emit(0xBF, 0x10 + i*2, 0x90, 0x3E)
    emit(0x99, 0x00 + i*2, 0x2F)
emit(0x60)                       # RTS

for off, name, add, kind in fixups:
    v = labels[name] + add
    if kind == 'abs':
        code[off], code[off+1] = v & 0xFF, v >> 8
    elif kind == 'rel':
        d = v - (ORG + off + 1)
        assert -128 <= d <= 127, (name, d)
        code[off] = d & 0xFF
    else:
        d = (v - (ORG + off + 2)) & 0xFFFF
        code[off], code[off+1] = d & 0xFF, d >> 8

# ------------------------------------------------------------ apply hooks ---
def patch(rom_off, data, expect=None):
    if expect is not None:
        assert bytes(ROM[rom_off:rom_off+len(expect)]) == bytes(expect), \
            'unexpected bytes at %06X: %s' % (rom_off, ROM[rom_off:rom_off+len(expect)].hex())
    ROM[rom_off:rom_off+len(data)] = data

ROM[BASE:BASE+len(code)] = code

# Dictionary escape moved from $1E to $0E.
#
# $1E was the kanji escape, and untranslated Japanese is full of it. Pointing it
# at the dictionary meant every untranslated string expanded whole English
# phrases mid-sentence and overran its window. $0E was unhandled - it fell
# through the CMP chain and ended the string - so nothing in the original script
# uses it, and it is safe to claim.
#
# The comparison it takes over is $01, a no-op that looped. Untranslated strings
# containing $01 now end early instead of looping, which is a far milder failure
# than a text leak.
patch(0x0815BB, bytes([0xC9, 0x0E, 0xF0, 0x10]),     # CMP #$0E / BEQ $95CF
      expect=[0xC9, 0x01, 0xF0, 0xBD])
patch(0x0815CF, bytes([0x4C, labels['DICT'] & 0xFF, labels['DICT'] >> 8]),
      expect=[0x20, 0x59, 0x98])
# $1E now consumes its argument and draws nothing, so leftover kanji escapes in
# untranslated text cost one skipped byte instead of a wrong glyph.
patch(0x081587, bytes([0xF0, 0x49]), expect=[0xF0, 0x46])          # BEQ $95D2
patch(0x0815D2, bytes([0x20, 0x59, 0x98, 0x80, 0xA5]),             # JSR $9859 / BRA $957C
      expect=[0xEB, 0xA9, 0x10, 0x80, 0x28])
# renderer: $90:9608  PHA / AND #$11   ->  JMP RENDER
patch(0x081608, bytes([0x4C, labels['RENDER'] & 0xFF, labels['RENDER'] >> 8]),
      expect=[0x48, 0x29, 0x11])
# newline: $90:96CC  JSR $9841  ->  JSR NEWNL
patch(0x0816CC, bytes([0x20, labels['NEWNL'] & 0xFF, labels['NEWNL'] >> 8]),
      expect=[0x20, 0x41, 0x98])
# bank select: $90:99F9  AND #$0011 -> AND #$0001   (kanji bank never selected)
patch(0x0819F9, bytes([0x29, 0x01, 0x00]), expect=[0x29, 0x11, 0x00])
# name field: $90:9777  JSR $9859 -> JSR NEWARG
patch(0x081777, bytes([0x20, labels['NEWARG'] & 0xFF, labels['NEWARG'] >> 8]),
      expect=[0x20, 0x59, 0x98])
# uploader: $90:9A6B onward -> JMP NEWUP
patch(0x081A6B, bytes([0x4C, labels['NEWUP'] & 0xFF, labels['NEWUP'] >> 8]),
      expect=[0xBD, 0x00, 0x2C])
# tilemap attribute: $90:9ACB  LDA $2C00,X / AND #$FC00 / ORA $A8
#                          ->  LDA #$2C00 / ORA $A8 / NOP NOP NOP
patch(0x081ACB, bytes([0x4C, labels['HIATTR'] & 0xFF, labels['HIATTR'] >> 8]) + b'\xea' * 5,
      expect=[0xBD, 0x00, 0x2C, 0x29, 0x00, 0xFC, 0x05, 0xA8])

# $97E8 - the decimal printer builds each digit with ADC #$A2, the Japanese
# font's glyph index for '0'. What $9605 takes is an index, not a script byte:
# RENDER does INC A to get h, and glyph h draws ASCII h + $1F. So '0' at ASCII
# $30 wants h = $11, hence index $10.
#
# The index is masked to seven bits downstream, so $A2 came out as $22 and drew
# ASCII $42 - digit d rendered as chr($42 + d). That is exactly what the
# screenshots show: 1 experience printed as 'C', a zero on the status screen as
# 'B'. It accounted for every number in the game.
patch(0x0817E9, bytes([0x10]), expect=[0xA2])

# $91:D033 and $91:D077 - the status screen's health and prayer separators.
# These live in a fourth text block at $08D023-$08D08E that is in none of the
# script blocks and has never been in the workbook. Byte $D9 is the full-width
# slash; the text path subtracts $20 for the index, so it drew ASCII $59 and the
# health read "295Y300". ASCII '/' is $2F. The slot length does not change.
#
# The rest of that block is cursor positions, stat icons and number fields, and
# it still needs folding into the spreadsheet properly.
patch(0x08D033, bytes([0x2F]), expect=[0xD9])
patch(0x08D077, bytes([0x2F]), expect=[0xD9])

# ---------------------------------------------------------- battle names --
# Monster names are glyph indices into a 16x16 katakana font (ROM $152000,
# LZSS, unpacks $2000 to $7E:4000) with the table at $153000: 63 entries of six
# bytes, null padded. The drawing routine is $81:F9D4 and the per-glyph DMA
# constants are all in $81:FA38-$FAB0:
#
#     $FA41  the sixth ASL      index * 64, the glyph stride
#     $FA74  LDX #$0020         top half transfer size
#     $FA98  LDA #$4020         bottom half source base
#     $FAA9  LDX #$0020         bottom half transfer size
#
# Halving those four turns each glyph into an 8x16 half-width cell and gives the
# block 256 slots instead of 128 - enough for a Latin font with no pair coding.
# Tried and reverted: the glyphs came out overlapping, because the VRAM
# destination step per glyph is computed at $FA18-$FA44 from the caller's tile
# coordinates and still assumes a two-tile-wide cell. That sum has to halve too,
# and the caller at $F9DC increments $084A and $084B once per glyph, so the
# stride is not a constant sitting in this routine.
#
# Also needed before the loop count at $F9D4 (CPX #$0006) can go to twelve: the
# name table restriped to 12-byte entries and relocated, since 63 * 12 = 756
# bytes will not fit where 378 do, and its stride lives inside $01:DD71.

# $9738 - the $09 cursor move, and $970B - the $07 window setup. Both opened
# with JSR $986A; they now go through CLOSE, which does the same thing after
# closing any half-open cell left behind by the previous field or screen.
patch(0x081738, bytes([0x20, labels['CLOSE'] & 0xFF, labels['CLOSE'] >> 8]),
      expect=[0x20, 0x6A, 0x98])
patch(0x08170B, bytes([0x20, labels['CLOSE'] & 0xFF, labels['CLOSE'] >> 8]),
      expect=[0x20, 0x6A, 0x98])
if __name__ == '__main__':
    print('new code %d bytes at ROM $%06X ($90:%04X)' % (len(code), BASE, ORG))
    for n in sorted(labels, key=lambda k: labels[k]):
        print('  %-10s $90:%04X' % (n, labels[n]))
    open('/home/claude/rom_hw.sfc', 'wb').write(bytes(ROM))

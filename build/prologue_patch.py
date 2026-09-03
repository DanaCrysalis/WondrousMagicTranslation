#!/usr/bin/env python3
"""Wondrous Magic - English intro poem and prologue.

The renderer in bank $A6 corrupts the last glyph of a record once a record runs
past about eight glyphs, so the half-width approach used for the dialogue engine
cannot be used here: it needs sixteen glyphs per record to fill a row.

Instead the prologue keeps its original timing exactly - eight full-width glyphs
per record, two records per row - and each of those sixteen cells holds TWO
half-width letters. That gives 32 characters per row at the original load. Only
the font source changes: one byte at $A6:881B and one at $A6:883A point the
uploader at a dedicated pair font at ROM $138000 (bank $27), built in the
original split layout, so the dialogue font at $0A8000 is left alone.

Stream format inside the RUX archive at ROM $132000 (decompressed to $7F:1DE7):
  word < $20    control: $0001 ends a record, $000A ends a row, $0000 ends a section
  word >= $20   glyph, index = word - $20
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths

import sys
import glyphs
from rux import decompress, compress

ROM = bytearray(open(paths.ROM_IN,'rb').read())
ARCHIVE = 0x132000
FONT = 0x138000                   # $27:8000, free
POEM_BODY = (0x0000, 0x07A8)
PROL_BODY = (0x07AA, 0x0F8C)

import sheet

# The poem and the prologue are authored on the `Intro crawl` sheet.
POEM, PROLOGUE = sheet.crawl()

COLS = 32                          # 16 glyph cells, two letters each
pairs = {'  ': 0}                  # glyph 0 stays blank


def glyph_of(pair):
    if pair not in pairs:
        pairs[pair] = len(pairs)
    return pairs[pair]


def row(text=''):
    assert len(text) <= COLS, text
    t = text.ljust(COLS)
    cells = [glyph_of(t[i:i+2]) for i in range(0, COLS, 2)]
    return ([g + 0x20 for g in cells[:8]] + [0x0001] +
            [g + 0x20 for g in cells[8:]] + [0x000A])


def build(lines, budget_words):
    out = []
    for t in lines:
        out += row(t)
    while len(out) + 18 <= budget_words:
        out += row()
    left = budget_words - len(out)
    if left == 1:                  # a lone word cannot form a record pair
        out = out[:-18]            # give one blank row back and pad instead
        left += 18
    if left:
        assert left >= 2, left
        n = left - 2
        blank = pairs['  '] + 0x20
        out += [blank] * min(n, 8) + [0x0001] + [blank] * max(0, n - 8) + [0x000A]
    assert len(out) == budget_words, (len(out), budget_words)
    return out


def write_font():
    for pr, g in pairs.items():
        glyphs.write_16(ROM, FONT, g, glyphs.pair(pr[0], pr[1]))


def patch(off, data, expect):
    assert bytes(ROM[off:off+len(expect)]) == bytes(expect), \
        'unexpected bytes at %06X: %s' % (off, ROM[off:off+len(expect)].hex())
    ROM[off:off+len(data)] = data


if __name__ == '__main__':
    blob = bytearray(decompress(bytes(ROM), ARCHIVE)[0])
    for (a, b), lines, name in ((POEM_BODY, POEM, 'poem'), (PROL_BODY, PROLOGUE, 'prologue')):
        stream = build(lines, (b - a) // 2)
        blob[a:b] = b''.join(w.to_bytes(2, 'little') for w in stream)
        print('%-9s %d bytes at blob $%04X' % (name, b - a, a))
    print('%d distinct pairs, font %d bytes' % (len(pairs), ((len(pairs) + 7) // 8) * 0x200))

    enc = compress(bytes(blob))
    assert decompress(enc, 0)[0] == bytes(blob)
    assert len(enc) <= 0x140000 - ARCHIVE
    ROM[ARCHIVE:ARCHIVE+len(enc)] = enc
    write_font()

    # the uploader's source bank: $15 (dialogue font) -> $27 (prologue pair font)
    patch(0x13081B, bytes([0x27]), [0x15])
    patch(0x130839, bytes([0x27]), [0x15])

    s = sum(bytes(ROM)) & 0xFFFF
    ROM[0x7FDE:0x7FE0] = s.to_bytes(2, 'little')
    ROM[0x7FDC:0x7FDE] = (s ^ 0xFFFF).to_bytes(2, 'little')
    open(paths.ROM_OUT, 'wb').write(bytes(ROM))
    print('archive %d bytes, checksum $%04X' % (len(enc), s))

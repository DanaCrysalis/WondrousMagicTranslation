#!/usr/bin/env python3
"""Glyph source.

Every font in the build now comes from one hand-drawn sheet,
`assets/halfwidth_font_sheet.png`, so the dialogue, the intro crawl and the
title screen cannot drift apart:

    half-width   $3E:9000   8x16, one glyph per cell     dialogue engine
    pairs        $27:8000   16x16, two letters per cell  intro crawl
    pairs        $0AB000    16x16, two letters per cell  menus and prompts
    singles      $0A8000    16x16, one letter centred    name entry chart

Sheet geometry: 128x96, 16 columns x 6 rows of 8x16 cells, no gaps, cell index
= row*16 + column, index h drawing ASCII h + $1F. Three levels: black is
background, mid-grey is the shadow, white is the body.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
from PIL import Image
import font_tool

SHEET = os.path.join(paths.ASSETS, 'halfwidth_font_sheet.png')

# Manufactured glyphs past the ASCII sheet. The descriptor carries a 7-bit glyph
# index, so h runs to 127 and the font region reaches $1F1FE0, just short of the
# dictionary table. Script byte = h + $1F, so these live at $80 upwards and are
# written as <G80> and so on.
SYMBOLS = {
    0x80: [                      # a house, for map nameplates
        '        ',
        '        ',
        '        ',
        '        ',
        '        ',
        '   #    ',
        '  ###   ',
        ' #####  ',
        '####### ',
        ' #   #  ',
        ' # # #  ',
        ' # # #  ',
        ' # # #  ',
        ' #####  ',
        '        ',
        '        ',
    ],
}
_cells = None


def _load():
    global _cells
    if _cells is not None:
        return _cells
    img = Image.open(SHEET).convert('RGB')
    assert img.size == (128, 96), 'sheet must be 128x96, got %dx%d' % img.size
    p = img.load()
    _cells = {}
    for h in range(96):
        ox, oy = (h % 16) * 8, (h // 16) * 16
        _cells[h] = [[font_tool.snap(p[ox + x, oy + y]) for x in range(8)]
                     for y in range(16)]
    return _cells


def half(ch):
    """8x16 matrix for one character. h = ASCII - $1F."""
    b = ord(ch)
    if b in SYMBOLS:
        return [[3 if c == '#' else 0 for c in row] for row in SYMBOLS[b]]
    return _load().get(b - 0x1F, [[0] * 8 for _ in range(16)])


def blank16():
    return [[0] * 16 for _ in range(16)]


def pair(a, b=' '):
    """16x16 holding two half-width letters side by side."""
    px = blank16()
    for i, ch in enumerate((a, b)):
        if ch == ' ':
            continue
        g = half(ch)
        for y in range(16):
            for x in range(8):
                px[y][i * 8 + x] = g[y][x]
    return px


def single(ch):
    """16x16 with one letter centred - the name entry chart picks whole cells."""
    px = blank16()
    if ch == ' ':
        return px
    g = half(ch)
    for y in range(16):
        for x in range(8):
            px[y][4 + x] = g[y][x]
    return px


def write_half(rom, base, count=128):
    """Linear 8x16 font: glyph h at base + h*32, top tile then bottom."""
    for h in range(count):
        ch = chr(h + 0x1F)
        px = half(ch) if (0 < h < 96 or ord(ch) in SYMBOLS) else [[0] * 8 for _ in range(16)]
        o = base + h * 32
        for part in (0, 1):
            for y in range(8):
                p0 = p1 = 0
                for x in range(8):
                    v = px[part * 8 + y][x]
                    p0 |= (v & 1) << (7 - x)
                    p1 |= ((v >> 1) & 1) << (7 - x)
                rom[o + part * 16 + y * 2] = p0
                rom[o + part * 16 + y * 2 + 1] = p1


def write_16(rom, base, g, px):
    """16x16 glyph in the split layout the Japanese font used:
    (g>>3)*$200 + (g&7)*32, top row of tiles there, bottom row at +$100."""
    o = base + (g >> 3) * 0x200 + (g & 7) * 32
    for part in (0, 1):
        for tx in (0, 1):
            dst = o + part * 0x100 + tx * 16
            for y in range(8):
                p0 = p1 = 0
                for x in range(8):
                    v = px[part * 8 + y][tx * 8 + x]
                    p0 |= (v & 1) << (7 - x)
                    p1 |= ((v >> 1) & 1) << (7 - x)
                rom[dst + y * 2] = p0
                rom[dst + y * 2 + 1] = p1

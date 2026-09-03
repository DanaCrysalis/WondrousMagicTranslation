#!/usr/bin/env python3
"""Wondrous Magic - half-width font sheet export / import.

The dialogue font lives at ROM $0A8000, glyph h at h*32: 16 bytes for the top
8x8 tile then 16 bytes for the bottom one, 2bpp. Glyph h draws ASCII h + $1F,
so h=1 is space and h=95 is '~'. Glyph 0 is the "cell not written" blank and
h=96 is the half-width space the dialogue script uses; both stay empty.

Sheet geometry - keep this exact or the import will not line up:

    128 x 96 pixels, no border, no gaps
    16 columns x 6 rows of 8x16 cells
    cell index = row*16 + column, index 0 top-left, reading left to right
    index h holds ASCII h + $1F

Colours. The font is 2bpp and the game only uses three of the four:

    #000000  transparent / background   (0)
    #808080  shadow                     (1)
    #FFFFFF  body                       (3)

On import anything is snapped to the nearest of those three by brightness, so
antialiased edges from a paste are fine - they land on the shadow colour.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths

from PIL import Image, ImageDraw

FONT = 0x1F1000                   # half-width ASCII font, $3E:9000
COLS, ROWS = 16, 6
CELL_W, CELL_H = 8, 16
LEVELS = {0: (0, 0, 0), 1: (128, 128, 128), 3: (255, 255, 255)}


def read_glyph(rom, h):
    o = FONT + h * 32
    px = [[0] * 8 for _ in range(16)]
    for half in (0, 1):
        for y in range(8):
            p0, p1 = rom[o + half*16 + y*2], rom[o + half*16 + y*2 + 1]
            for x in range(8):
                px[half*8 + y][x] = ((p0 >> (7-x)) & 1) | (((p1 >> (7-x)) & 1) << 1)
    return px


def write_glyph(rom, h, px):
    o = FONT + h * 32
    for half in (0, 1):
        for y in range(8):
            p0 = p1 = 0
            for x in range(8):
                v = px[half*8 + y][x]
                p0 |= (v & 1) << (7-x)
                p1 |= ((v >> 1) & 1) << (7-x)
            rom[o + half*16 + y*2] = p0
            rom[o + half*16 + y*2 + 1] = p1


def export(rom, path):
    img = Image.new('RGB', (COLS*CELL_W, ROWS*CELL_H), (0, 0, 0))
    p = img.load()
    for h in range(COLS*ROWS):
        px = read_glyph(rom, h)
        ox, oy = (h % COLS)*CELL_W, (h // COLS)*CELL_H
        for y in range(CELL_H):
            for x in range(CELL_W):
                p[ox+x, oy+y] = LEVELS.get(px[y][x], (0, 0, 0))
    img.save(path)
    return img


def snap(rgb):
    v = (rgb[0]*299 + rgb[1]*587 + rgb[2]*114) // 1000
    return 0 if v < 64 else (1 if v < 192 else 3)


def load(rom, path):
    img = Image.open(path).convert('RGB')
    assert img.size == (COLS*CELL_W, ROWS*CELL_H), \
        'sheet must be %dx%d, got %dx%d' % (COLS*CELL_W, ROWS*CELL_H, *img.size)
    p = img.load()
    for h in range(COLS*ROWS):
        ox, oy = (h % COLS)*CELL_W, (h // COLS)*CELL_H
        px = [[snap(p[ox+x, oy+y]) for x in range(CELL_W)] for y in range(CELL_H)]
        write_glyph(rom, h, px)


def guide(rom, path, scale=6):
    """Reference only - do not edit this one, it has grid lines and labels."""
    w, h_ = COLS*(CELL_W*scale+1)+1, ROWS*(CELL_H*scale+1)+1
    img = Image.new('RGB', (w, h_ + 14), (24, 24, 28))
    d = ImageDraw.Draw(img)
    d.text((2, 2), 'index h -> ASCII h+$1F   (h=1 space ... h=95 tilde)', fill=(200, 200, 210))
    p = img.load()
    for h in range(COLS*ROWS):
        gx, gy = (h % COLS)*(CELL_W*scale+1)+1, (h // COLS)*(CELL_H*scale+1)+15
        px = read_glyph(rom, h)
        for y in range(CELL_H):
            for x in range(CELL_W):
                c = LEVELS.get(px[y][x], (0, 0, 0))
                for sy in range(scale):
                    for sx in range(scale):
                        p[gx+x*scale+sx, gy+y*scale+sy] = c
    for c in range(COLS+1):
        d.line([(c*(CELL_W*scale+1), 14), (c*(CELL_W*scale+1), h_+13)], fill=(70, 70, 80))
    for r in range(ROWS+1):
        d.line([(0, 14+r*(CELL_H*scale+1)), (w, 14+r*(CELL_H*scale+1))], fill=(70, 70, 80))
    img.save(path)


if __name__ == '__main__':
    rom = bytearray(open(paths.ROM_OUT,'rb').read())
    export(rom, os.path.join(paths.ASSETS,'halfwidth_font_sheet.png'))
    guide(rom, os.path.join(paths.ASSETS,'halfwidth_font_guide.png'))
    # round-trip check
    before = bytes(rom[FONT:FONT + COLS*ROWS*32])
    load(rom, os.path.join(paths.ASSETS,'halfwidth_font_sheet.png'))
    print('round-trip:', 'OK' if bytes(rom[FONT:FONT + COLS*ROWS*32]) == before else 'MISMATCH')

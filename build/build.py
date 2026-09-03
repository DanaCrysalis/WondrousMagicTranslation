#!/usr/bin/env python3
"""Wondrous Magic - full build from a clean ROM.

  1. half-width dialogue engine   (hw_patch)      code at $90:E900
  2. half-width ASCII font        ROM $1F1000     $3E:9000, 97 glyphs of 32 bytes
  3. English intro poem/prologue  RUX archive $132000 + pair font $138000
  4. Blocks A, B and C plus the dictionary at $1F2000
  5. Title screen and name entry

The Japanese font at $0A8000 is deliberately left untouched. The title screen and
the name entry screen read it directly - they are not part of the text engine, and
overwriting it was what garbled them.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths

import sys
from PIL import Image, ImageDraw, ImageFont

ROM_IN = paths.ROM_IN
ROM_OUT = paths.ROM_OUT
HW_FONT = 0x1F1000                # $3E:9000
TTF = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 11)


def write_halfwidth_font(rom):
    """Glyph h at HW_FONT + h*32: top 8x8 tile then bottom. h draws ASCII h + $1F,
    so h=1 is space; h=0 and h=96 stay blank."""
    for h in range(97):
        img = Image.new('L', (8, 16), 0)
        if 0 < h < 96:
            ImageDraw.Draw(img).text((0, 2), chr(h + 0x1F), font=TTF, fill=255)
        px = [[3 if img.getpixel((x, y)) > 110 else 0 for x in range(8)] for y in range(16)]
        o = HW_FONT + h * 32
        for half in (0, 1):
            for y in range(8):
                p0 = p1 = 0
                for x in range(8):
                    v = px[half*8 + y][x]
                    p0 |= (v & 1) << (7-x)
                    p1 |= ((v >> 1) & 1) << (7-x)
                rom[o + half*16 + y*2] = p0
                rom[o + half*16 + y*2 + 1] = p1


def checksum(rom):
    s = sum(bytes(rom)) & 0xFFFF
    rom[0x7FDE:0x7FE0] = s.to_bytes(2, 'little')
    rom[0x7FDC:0x7FDE] = (s ^ 0xFFFF).to_bytes(2, 'little')
    return s


if __name__ == '__main__':
    import hw_patch, prologue_patch as pp
    from rux import decompress, compress

    # 1. engine - hw_patch applies its hooks to a clean ROM when imported
    rom = hw_patch.ROM
    assert all(b == 0xFF for b in rom[HW_FONT:HW_FONT + 97*32]), 'font space not free'

    # 2. font
    write_halfwidth_font(rom)

    # 3. the opening scene now comes from script_b like the rest of the story

    # 4. intro crawl
    pp.ROM = rom
    blob = bytearray(decompress(bytes(rom), pp.ARCHIVE)[0])
    for (a, b), lines in ((pp.POEM_BODY, pp.POEM), (pp.PROL_BODY, pp.PROLOGUE)):
        stream = pp.build(lines, (b - a) // 2)
        blob[a:b] = b''.join(w.to_bytes(2, 'little') for w in stream)
    enc = compress(bytes(blob))
    assert decompress(enc, 0)[0] == bytes(blob)
    rom[pp.ARCHIVE:pp.ARCHIVE + len(enc)] = enc
    pp.write_font()
    for off, data, expect in ((0x13081B, b'\x27', b'\x15'), (0x130839, b'\x27', b'\x15')):
        assert bytes(rom[off:off+1]) == expect, '%06X' % off
        rom[off:off+1] = data

    # 5. blocks A and C
    import script_a, script_b, script_c, dictionary, wmtool
    text_a, missing = script_a.build()
    assert not missing, missing[:4]
    strings = dict(script_c.TEXT)
    strings.update(text_a)
    strings.update(script_b.TEXT)
    budgets = []
    for off, en in sorted(strings.items()):
        _, end = wmtool.decode(off)
        budgets.append((en, end - off))
    import re
    for off, en in sorted(script_c.TEXT.items()):        # window rows are whole cells
        for line in en.split('\n'):
            m = re.match(r'^<EEA>(.*)<EFA>', line)
            if m:
                w = wmtool.cells(m.group(1))
                assert w == int(w), '%06X: row is %s cells, not whole' % (off, w)
    entries = dictionary.fit(budgets, dictionary.choose([t for t, _ in budgets], count=300))
    dsize = dictionary.write(rom, entries)
    for off, en in sorted(strings.items()):
        _, end = wmtool.decode(off)
        data = dictionary.encode(en, entries)
        assert len(data) <= end - off, '%06X over budget' % off
        rom[off:off + len(data)] = data
        for i in range(off + len(data), end):
            rom[i] = 0x00
    print('blocks A+B+C: %d strings, dictionary %d entries / %d bytes'
          % (len(strings), len(entries), dsize))

    # 6. title screen and name entry
    import systext
    npairs = systext.apply(rom)
    print('crawl pairs %d, system pairs %d, archive %d bytes, checksum $%04X'
          % (len(pp.pairs), npairs, len(enc), checksum(rom)))
    open(ROM_OUT, 'wb').write(bytes(rom))

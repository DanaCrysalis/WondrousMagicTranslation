#!/usr/bin/env python3
"""Wondrous Magic - full build from a clean ROM.

  1. half-width dialogue engine   (hw_patch)      code at $90:E900
  2. half-width ASCII font        ROM $1F1000     $3E:9000, 97 glyphs of 32 bytes
  3. English intro poem/prologue  RUX archive $132000 + pair font $138000
  4. Blocks A, B and C plus the dictionary at $1F2000
  5. Title screen and name entry

All English comes from data/Wondrous_Magic_script.xlsx by way of build/sheet.py.
There are no script_*.py tables any more.

The Japanese font at $0A8000 is deliberately left untouched. The title screen and
the name entry screen read it directly - they are not part of the text engine, and
overwriting it was what garbled them.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
import glyphs

import sys

ROM_IN = paths.ROM_IN
ROM_OUT = paths.ROM_OUT
HW_FONT = 0x1F1000                # $3E:9000


def write_halfwidth_font(rom):
    glyphs.write_half(rom, HW_FONT)


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

    # 5. blocks A, B and C - all of it out of the workbook
    import sheet, dictionary, wmtool, blockb, blockd
    strings = sheet.text()
    block_c = {off: en for off, en in strings.items() if off < 0x090EF6}
    # Blocks A and C are written back in place, so their lengths are fixed and
    # the dictionary has to make them fit. Block B is repacked and its pointer
    # table rewritten, so it has no per-string budget at all - it still feeds
    # the entry search, it just does not constrain it.
    # Blocks A, C and E are written back in place. Blocks B and D are repacked
    # against their own pointer tables, so their lengths are free.
    loose = set(range(blockd.START, blockd.END)) | {blockb.START}
    fixed = {off: en for off, en in strings.items()
             if off < blockb.START and off not in loose}
    budgets = []
    for off, en in sorted(fixed.items()):
        _, end = wmtool.decode(off)
        budgets.append((en, end - off))
    import re
    for off, en in sorted(block_c.items()):              # window rows are whole cells
        for line in en.split('\n'):
            m = re.match(r'^<EEA>(.*)<EFA>', line)
            if m:
                w = wmtool.cells(m.group(1))
                assert w == int(w), '%06X: row is %s cells, not whole' % (off, w)
    for off in range(0x0909A0, 0x090A5C):               # map nameplate is ten
        if off in block_c:                              # half-width characters
            w = wmtool.cells(block_c[off]) * 2
            assert w <= 10, '%06X: nameplate %s wide' % (off, w)
    free = [en for off, en in sorted(strings.items()) if off not in fixed]
    # `free` is everything that gets repacked, so the ceiling is the sum of the
    # room both packers have. They each assert their own extents afterwards.
    room = (blockb.LIMIT - blockb.START) + sum(hi - lo for lo, hi in blockd.EXTENTS)
    entries = dictionary.fit_mixed(budgets, free, room)
    dsize = dictionary.write(rom, entries)
    over = []
    for off, en in sorted(fixed.items()):
        _, end = wmtool.decode(off)
        data = dictionary.encode(en, entries)
        if len(data) > end - off:
            over.append((len(data) - (end - off), off, en))
            continue
        rom[off:off + len(data)] = data
        for i in range(off + len(data), end):
            rom[i] = 0x00
    if over:
        over.sort(reverse=True)
        print('OVER BUDGET: %d of %d fixed-length strings, dictionary %d/%d entries'
              % (len(over), len(fixed), len(entries), dictionary.MAX_ENTRIES))
        for n, off, en in over[:25]:
            print('  $%06X  +%d bytes  %r' % (off, n, en[:60]))
        raise SystemExit('nothing written')
    used, spare = blockb.build(rom, strings, entries)
    dused, dspare = blockd.build(rom, strings, entries)
    print('blocks A+C: %d strings in place, dictionary %d entries / %d bytes'
          % (len(fixed), len(entries), dsize))
    print('block B: %d strings repacked into %d bytes, %d spare, table rewritten'
          % (sum(1 for o in strings if o >= blockb.START), used, spare))
    print('block D: %d hints repacked into %d bytes, %d spare, table rewritten'
          % (sum(1 for o in strings if blockd.START <= o < blockd.END), dused, dspare))

    # 6. title screen and name entry
    import systext
    npairs = systext.apply(rom)
    print('crawl pairs %d, system pairs %d, archive %d bytes, checksum $%04X'
          % (len(pp.pairs), npairs, len(enc), checksum(rom)))
    open(ROM_OUT, 'wb').write(bytes(rom))

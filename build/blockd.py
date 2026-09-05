#!/usr/bin/env python3
"""Block D - Rinkle's area hints, and the small table that addresses them.

`$0930F7` holds 51 uint16 entries, each an absolute `$92:xxxx` address, and each
one lands exactly on a string start: 51 entries, 51 strings, nothing orphaned.
That is the same shape as the item table at `$090F00`, and it means the hints do
not have to keep their lengths - rewrite the table and they can sit anywhere in
bank $92.

English runs about 1.5x the Japanese here, which the original 2,005-byte slot
will not take, so the pack runs across two extents: the slot itself, and the
2,363 bytes of $FF left after block A ends at `$0976C5`. The table is absolute,
so a string can be in either one and nothing needs to know which.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
import wmtool
import dictionary

TABLE = 0x0930F7                 # 51 x uint16, absolute $92:xxxx
COUNT = 51
START = 0x09316E                 # the strings as they stand
END = 0x093943
SPARE = (0x0976C5, 0x098000)     # free space after block A, same bank

EXTENTS = [(START, END), SPARE]


def walk():
    out, p = [], START
    while p < END:
        _toks, q = wmtool.decode(p)
        out.append((p, q))
        p = q
    return out


def old_table():
    return [wmtool.snes2pc(0x92, wmtool.ROM[TABLE + i*2] | (wmtool.ROM[TABLE + i*2 + 1] << 8))
            for i in range(COUNT)]


def build(rom, strings, entries):
    """Repack the hints across both extents and rewrite the table."""
    spans = walk()
    starts = {a for a, _ in spans}
    targets = old_table()
    for t in targets:
        if t not in starts:
            raise SystemExit('$%06X is not a hint string start' % t)

    blobs = [bytearray() for _ in EXTENTS]
    place = {}
    for a, b in spans:
        en = strings.get(a)
        data = rom[a:b] if en is None else dictionary.encode(en, entries)
        for k, (lo, hi) in enumerate(EXTENTS):
            if len(blobs[k]) + len(data) <= hi - lo:
                place[a] = lo + len(blobs[k])
                blobs[k] += data
                break
        else:
            raise SystemExit('block D: no room left for $%06X' % a)

    for k, (lo, hi) in enumerate(EXTENTS):
        for i in range(lo, hi):
            rom[i] = 0xFF
        rom[lo:lo + len(blobs[k])] = blobs[k]

    for i, t in enumerate(targets):
        addr = wmtool.pc2snes(place[t])[1]
        rom[TABLE + i*2:TABLE + i*2 + 2] = addr.to_bytes(2, 'little')

    used = sum(len(b) for b in blobs)
    room = sum(hi - lo for lo, hi in EXTENTS)
    return used, room - used

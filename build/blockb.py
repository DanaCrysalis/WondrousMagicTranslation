#!/usr/bin/env python3
"""Block B is table-driven, so its strings do not have to keep their length.

`$90:94CA` turns a scene index into a script pointer:

    TXA / ASL / TAX          index * 2
    CLC
    LDA #$8000
    ADC $138000,X            16-bit entry, CPU $13:8000 = ROM $098000
    ORA #$8000               back into the top half of the bank
    TAX
    LDA #$13 / ADC #$00      bank $93, plus the carry out of the add

So the entry is just `target - $098000`, and the carry is what lets block B run
from bank $93 into $94 with only two bytes per entry. The table is 416 entries at
ROM $098000-$09833F, immediately before block B itself.

Every route into block B goes through that routine - of the 60 call sites of the
interpreter, not one loads bank $93 or $94 as a literal. So rewriting the table
is enough: strings can be any length and sit anywhere in $098340-$0A7FFF, which
is what the 16-bit displacement reaches.

Four entries point into the middle of a string rather than at its start, which
the engine is perfectly happy to do. Those strings are encoded in pieces so the
resume points can be recomputed; see SPLITS.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
import wmtool
import dictionary

TABLE = 0x098000                 # 416 x uint16, displacement from TABLE
COUNT = 416
START = 0x098340                 # first string, right after the table
LIMIT = 0x0A8000                 # last address a 16-bit displacement reaches
END = 0x0A5625                   # last real string ends here; $0A5625 itself is
                                 # a single filler byte with no terminator after
                                 # it, so decoding from it runs 8K into the void

# A string that an entry points into the middle of has to be encoded in pieces,
# or there is no way to know where the resume point lands. Each marker is
# (text, nth occurrence) and starts a new piece. The order matches the order of
# the mid-string entries into that string.
SPLITS = {
    0x0A225C: [(' for nothing!\n', 1)],
    0x0A528F: [('<EE9><EE9>', 3)],
    0x0A42A6: [('\u3000\u3000"Equip Weapon"', 1), ('\u3000\u3000to put it on.', 1)],
}


def walk():
    """Block B as it stands in the Japanese ROM: [(offset, end)]."""
    out, p = [], START
    while p < END:
        _toks, q = wmtool.decode(p)
        out.append((p, q))
        p = q
    return out


def old_table():
    """The 416 entries, resolved to ROM offsets."""
    return [TABLE + (wmtool.ROM[TABLE + i*2] | (wmtool.ROM[TABLE + i*2 + 1] << 8))
            for i in range(COUNT)]


def _pieces(text, marks):
    """Cut `text` at each marker, keeping the marker at the head of its piece."""
    cuts = []
    for mark, nth in marks:
        i = -1
        for _ in range(nth):
            i = text.index(mark, i + 1)
        cuts.append(i)
    if cuts != sorted(cuts):
        raise SystemExit('splits out of order')
    out, last = [], 0
    for c in cuts:
        out.append(text[last:c]); last = c
    out.append(text[last:])
    return out


def build(rom, strings, entries):
    """Repack block B and rewrite its pointer table. Returns (used, spare)."""
    spans = walk()
    starts = {a for a, _ in spans}
    targets = old_table()

    # every entry has to land on a string start or on a declared split
    mids = {}
    for a, b in spans:
        if a in SPLITS:
            mids[a] = [t for t in sorted(set(targets)) if a < t < b]
    for t in targets:
        if t in starts or t == 0x098338:
            continue
        owner = max((a for a, b in spans if a < t < b), default=None)
        if owner is None or owner not in SPLITS:
            raise SystemExit('$%06X is a mid-string entry with no split declared' % t)

    blob = bytearray()
    place = {}                                   # old offset -> new offset
    inner = {}                                   # old mid target -> new offset
    for a, b in spans:
        place[a] = START + len(blob)
        en = strings.get(a)
        if en is None:                           # never translated - keep the bytes
            blob += rom[a:b]
            continue
        if a in SPLITS:
            parts = _pieces(en, SPLITS[a])
            if len(mids[a]) != len(parts) - 1:
                raise SystemExit('$%06X: %d entries point inside it but %d splits'
                                 % (a, len(mids[a]), len(parts) - 1))
            for k, part in enumerate(parts):
                if k:
                    inner[mids[a][k - 1]] = START + len(blob)
                data = dictionary.encode(part, entries)
                if k < len(parts) - 1:
                    data = data[:-1]             # only the last piece terminates
                blob += data
        else:
            blob += dictionary.encode(en, entries)

    used = len(blob)
    if START + used > LIMIT:
        raise SystemExit('block B needs %d bytes, %d over the $%06X ceiling'
                         % (used, START + used - LIMIT, LIMIT))

    for i in range(START, LIMIT):
        rom[i] = 0xFF
    rom[START:START + used] = blob

    for i, t in enumerate(targets):
        if t == 0x098338:                        # dead slot, points into the table
            new = t
        elif t in place:
            new = place[t]
        else:
            new = inner[t]
        d = new - TABLE
        assert 0 <= d <= 0xFFFF, 'entry %d out of reach' % i
        rom[TABLE + i*2:TABLE + i*2 + 2] = d.to_bytes(2, 'little')

    return used, LIMIT - START - used

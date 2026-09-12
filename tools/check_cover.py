#!/usr/bin/env python3
"""Find text that no longer covers the text it is drawn over.

    python3 tools/check_cover.py                  # the windows that are never cleared
    python3 tools/check_cover.py 0A4509 0A4C8C    # any ROM range

Menu and shop windows are not cleared between one string and the next. They did
not need to be: every Japanese glyph was one whole cell, so each line physically
covered the line before it, and every string left the cursor in the same place
the next one expected. Half-width English covers half as much per character, so
a line narrower than its Japanese original leaves the tail of the last string on
screen - the shop greeting running into the shop menu, the storage, appraiser
and temple windows keeping stale words, a submenu header keeping the m of "Drop
Item" behind "Use Item".

So the rule is: **an English line must be at least as many cells wide as the
Japanese line it replaces.** Pad with `\u3000`, which is one whole blank cell and
one byte, or with a space, which is half a cell. This lists every line that is
not.

It is not a rule about prose - a dialogue box opened with <PAGE> is already
blank and nothing under it needs covering, so lines after a <PAGE> are skipped.
It is a rule about windows that stay on screen while their contents change.

Two families are reported and deliberately left short, so this is a report and
not a gate - it does not fail the build:

  * the spell names. Padding them would fix the list and spoil "Casting <NAME>."
    and "Learned <NAME> Lev.N!", which print the same string inline. The menu
    pads the name field itself, the way every <NAME:sWW> field does.
  * the first line of a spell description - name, level and cost. The Japanese
    ran it to fifteen cells, past the fourteen the panel holds, so it is no
    measure of anything. Every spell's first line has the same layout and the
    same width, so they cover each other regardless.
"""
import math, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
import book
import sheet

TOK = re.compile(r'<([^>]*)>')
WINDOW = 14.0          # cells of text between the frame columns

# The windows that hold their contents while the text inside them changes.
RANGES = [
    (0x0907ED, 0x09087F, 'block C - submenu headers, money and price fields'),
    (0x090AB4, 0x090EF6, 'block C - spell names and the description panel'),
    (0x0A4509, 0x0A4C8C, 'block B - appraiser, antiquary, shop, storage, temple, inn'),
]


def cells(line, japanese=False):
    """Cell width of one line. Half-width ASCII is half a cell, all else one.

    <NAME:sWW> and <NUM7:sWW> pad to WW cells and grow past it when the value
    needs more, so WW is the floor and that is what is counted here.
    """
    n, i = 0.0, 0
    while i < len(line):
        c = line[i]
        if c == '<':
            j = line.index('>', i)
            body = line[i + 1:j]
            i = j + 1
            if body[0] in 'ES':
                n += 1.0                              # frame tile, or $1F icon
            elif body[0] == 'G':
                n += 0.5                              # manufactured half glyph
            elif body.startswith(('NAME:', 'NUM7:', 'NUM8:')):
                n += int(body.split(':')[1][2:], 16)
            continue
        i += 1
        if c == '\n':
            continue
        if japanese or c == '\u3000' or ord(c) > 0x2000:
            n += 1.0
        else:
            n += 0.5


        continue
    return n


MAXNAME = {0x03: 6.0,      # item names, the longest is twelve characters
           0x02: 4.0,      # party names
           0x04: 5.0,      # spell names
           0x08: 1.0}      # the money mark


def widest(line):
    """The widest this line can render, with every field at its longest.

    <NAME:sWW> pads to WW cells but grows past it whenever the name needs more,
    and the name is not known until the game runs. The prefix is rounded up to a
    whole cell first: the name field closes any half-open cell before it starts.
    """
    m = re.search(r'<NAME:([0-9A-Fa-f]{2})([0-9A-Fa-f]{2})>', line)
    if not m:
        return cells(line)
    slot, ww = int(m.group(1), 16), int(m.group(2), 16)
    return (math.ceil(cells(line[:m.start()]))
            + max(ww, MAXNAME.get(slot, ww))
            + widest(line[m.end():]))


def check(rows, lo, hi):
    short, over = [], []
    for r in rows:
        r = list(r) + [None] * 10
        if not r[2] or str(r[2]) == 'ROM':
            continue
        off = int(str(r[2]).lstrip('$'), 16)
        if not (lo <= off < hi):
            continue
        jp, en = r[6] or '', r[7] or ''
        if not en:
            continue
        jl, el = jp.split('\n'), en.split('\n')
        paged = False
        for k, line in enumerate(el):
            if '<PAGE>' in line:
                paged = True
            if paged or k >= len(jl):
                continue
            # A line whose width is decided at runtime cannot be padded: the
            # Japanese sized it so the longest name just fits, so there is
            # nothing spare, and padding it only pushes the tail onto the
            # border. Report it if its worst case does not fit the window.
            if '<NAME:' in line:
                w = widest(line)
                if w > WINDOW:
                    over.append((r[0], off, k, WINDOW, w, line))
                continue
            want, got = cells(jl[k], True), cells(line)
            if got < want:
                short.append((r[0], off, k, want, got, line))
    return short, over


def main(argv):
    rows = book.read(sheet.BOOK)['Script']
    ranges = ([(int(argv[0], 16), int(argv[1], 16), 'given range')]
              if len(argv) == 2 else RANGES)
    total = 0
    for lo, hi, name in ranges:
        short, over = check(rows, lo, hi)
        for ident, off, k, win, w, line in over:
            print('  !! %-6s $%06X line %d  can reach %4.1f cells in a %.0f-cell '
                  'window  %r' % (ident, off, k, w, win, line[:44]))
        print('=== %s: %d lines short' % (name, len(short)))
        for ident, off, k, want, got, line in short:
            print('  %-6s $%06X line %d  wants %4.1f cells, covers %4.1f  %r'
                  % (ident, off, k, want, got, line[:44]))
        total += len(short)
    print('\n%d lines short in total' % total)
    return 1 if total else 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))

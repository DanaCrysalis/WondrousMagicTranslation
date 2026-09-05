#!/usr/bin/env python3
"""Wondrous Magic - title screen and name entry in English.

Both screens run off a shared text layer at $7E:2000 driven by $82:BD68, which
indexes the Japanese font at $0A8000 as one flat sheet: code $000-$0BF is the
text bank, $0C0-$1BF the kanji bank. Their strings live at ROM $141000
($A8:9000) as 16-bit words with the stored value being code + 1, $0000 ending
each string.

Nothing else reads $0A8000 any more - the dialogue engine has its own font at
$3E:9000 and the intro crawl at $27:8000 - so both halves are free:

    code $001-$05E   single Latin letter, ASCII code + $20   (name entry chart)
    code $0C0-$1BF   two half-width letters                  (menus and prompts)

The single-letter half has to be exactly ASCII - $20, because confirming a name
stores the chart cell's code + $20 as a script byte at $7E:3280, and the dialogue
engine renders script byte b as ASCII b. Verified against a savestate: a name of
three あ (chart code $01) stored as 21 21 21.

Every string is rewritten within its original byte length and padded, so the
table's layout does not move.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths

import sys
import glyphs

FONT = 0x0A8000
TABLE = 0x141000
ATTR = 0x1C00

import sheet

# Both tables now live in the workbook: the `Title screen` and `Name entry`
# sheets. Row lengths in the grid are load-bearing, so they are checked here
# rather than trusted - a spreadsheet editor will happily eat a trailing space.
STRINGS = sheet.title()
CHART_ROWS = sheet.chart()

_EXPECT = [14, 14, 14, 14, 14, 0, 13, 12]
assert len(CHART_ROWS) == len(_EXPECT), \
    'Name entry sheet has %d rows, expected %d' % (len(CHART_ROWS), len(_EXPECT))
for _i, (_row, _n) in enumerate(zip(CHART_ROWS, _EXPECT)):
    assert len(_row) == _n, \
        'Name entry row %d is %d cells, must be %d (trailing spaces matter)' \
        % (_i + 1, len(_row), _n)

pairs = {}


def pair_code(pair):
    if pair not in pairs:
        pairs[pair] = 0xC0 + len(pairs)
        assert pairs[pair] <= 0x1BF, 'out of pair codes'
    return pairs[pair]


def encode_prose(text):
    t = text if len(text) % 2 == 0 else text + ' '
    return [pair_code(t[i:i+2]) for i in range(0, len(t), 2)]


def string_len(rom, off):
    n = 0
    while rom[off + n] or rom[off + n + 1]:
        n += 2
    return n + 2


def put(rom, off, codes, budget):
    """Write codes, pad with blank pairs, keep the byte length identical.

    Every one of these strings ends in a control word - $30E raw, $30D once the
    +1 is taken off, the same row terminator the name entry chart uses. Writing
    blanks over it left the row unterminated, which is what took the chunks out
    of the Options border. Hold any trailing control back and put it on the end.
    """
    blank = pair_code('  ')
    cells = budget // 2 - 1
    orig = [rom[off + i] | rom[off + i + 1] << 8 for i in range(0, budget - 2, 2)]
    tail = []
    while orig and ((orig[-1] - 1) & 0x3FF) >= 0x1C0:
        tail.insert(0, orig.pop())
    words = [(c + ATTR + 1) & 0xFFFF for c in codes]
    assert len(words) + len(tail) <= cells, (off, len(words), len(tail), cells)
    words += [(blank + ATTR + 1) & 0xFFFF] * (cells - len(words) - len(tail))
    words += tail
    data = b"".join(w.to_bytes(2, "little") for w in words)
    rom[off:off + budget] = data + b"\x00\x00"


def draw_single(ch):
    img = Image.new('L', (16, 16), 0)
    if ch != ' ':
        ImageDraw.Draw(img).text((4, 2), ch, font=TTF, fill=255)
    return img


def draw_pair(pair):
    img = Image.new('L', (16, 16), 0)
    d = ImageDraw.Draw(img)
    for i, ch in enumerate(pair):
        if ch != ' ':
            d.text((i * 8, 2), ch, font=TTF, fill=255)
    return img


def write_glyph(rom, g, img):
    px = [[3 if img.getpixel((x, y)) > 110 else 0 for x in range(16)] for y in range(16)]
    base = FONT + (g >> 3) * 0x200 + (g & 7) * 32
    for half in (0, 1):
        for tx in (0, 1):
            dst = base + half * 0x100 + tx * 16
            for y in range(8):
                p0 = p1 = 0
                for x in range(8):
                    v = px[half * 8 + y][tx * 8 + x]
                    p0 |= (v & 1) << (7 - x)
                    p1 |= ((v >> 1) & 1) << (7 - x)
                rom[dst + y * 2] = p0
                rom[dst + y * 2 + 1] = p1


def apply(rom):
    # prose strings
    for off, text in STRINGS.items():
        put(rom, off, encode_prose(text), string_len(rom, off))

    # Both chart pages are ONE string each, with rows separated by control $30D
    # and a few symbol codes ($1C0+) parked at the ends of the last two rows.
    for page in (0x1410B8, 0x14118E):
        budget = string_len(rom, page)
        orig = [rom[page + i] | rom[page + i + 1] << 8 for i in range(0, budget - 2, 2)]
        rows, cur = [], []
        for w in orig:
            c = ((w - 1) & 0x3FF)
            if c == 0x30D:
                rows.append((cur, w)); cur = []
            else:
                cur.append(w)
        out = []
        for (words, ctrl), text in zip(rows, CHART_ROWS):
            keep = [w for w in words if ((w - 1) & 0x3FF) >= 0x1C0]   # symbol buttons
            n = len(words) - len(keep)
            t = text.ljust(n)[:n]
            out += [(ord(ch) - 0x20 + ATTR + 1) & 0xFFFF for ch in t]
            out += keep
            out.append(ctrl)
        for words, ctrl in rows[len(CHART_ROWS):]:
            out += words + [ctrl]
        data = b''.join(w.to_bytes(2, 'little') for w in out)
        assert len(data) + 2 == budget, (hex(page), len(data) + 2, budget)
        rom[page:page + budget] = data + b'\x00\x00'

    # single letters: code = ASCII - $20
    for c in range(0x01, 0x5F):
        glyphs.write_16(rom, FONT, c, glyphs.single(chr(c + 0x20)))
    # letter pairs
    for pr, g in pairs.items():
        glyphs.write_16(rom, FONT, g, glyphs.pair(pr[0], pr[1]))
    return len(pairs)

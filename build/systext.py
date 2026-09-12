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


# --------------------------------------------------------- the three buttons --
#
# The chart's last two rows carry three symbol codes that the chart string keeps
# verbatim, because $82:A67F dispatches on the code it reads back out of the
# text layer:
#
#     $206   delete    row 6, column 0     $82:A6A5 -> $82:A621, the backspace
#     $207   space     row 7, column 1     $82:A6B7, substitutes $BF, stored $20
#     $205   end       row 7, column 0     $82:A6C7, returns $FFFF, name accepted
#
# Changing the codes would mean changing that dispatch, so the codes stay and
# only the pictures change. They are not in the $0A8000 font: $82:BE9A resolves
# codes $200-$209 to bank $28 at $8C00, in the same interleaved 16x16 layout the
# text font uses, so glyphs.write_16 addresses them at index code - $1FB.
#
# Three letters will not fit across sixteen pixels side by side, so they are set
# 4x5 and stepped down the diagonal - SPC, DEL and END read top-left to
# bottom-right, with the same one-pixel shadow the chart letters have.

BUTTON_FONT = 0x140C00           # $28:8C00, codes $200-$209
BUTTONS = {0x205: 'END', 0x206: 'DEL', 0x207: 'SPC'}

MICRO = {
    'S': ('.###',
          '#...',
          '.##.',
          '...#',
          '###.'),
    'P': ('###.',
          '#..#',
          '###.',
          '#...',
          '#...'),
    'C': ('.###',
          '#...',
          '#...',
          '#...',
          '.###'),
    'D': ('###.',
          '#..#',
          '#..#',
          '#..#',
          '###.'),
    'E': ('####',
          '#...',
          '###.',
          '#...',
          '####'),
    'L': ('#...',
          '#...',
          '#...',
          '#...',
          '####'),
    'N': ('#..#',
          '##.#',
          '#.##',
          '#..#',
          '#..#'),
}


STEP = (5, 4)                    # 4x5 letters, three of them, 16x16 to fill

# C is the one letter whose 4x5 form opens with a blank column, so in the third
# slot it sat a pixel right of where END's D and DEL's L put their ink and SPC
# looked lopsided. Nudge the whole letter back by one.
NUDGE = {'C': -1}


def button(label):
    """16x16 with three 4x5 letters stepped down the diagonal.

    Shadow first and body over it, so a letter's shadow never eats the corner
    of the one below - the step is one pixel tighter than the letters are tall.
    """
    px = glyphs.blank16()
    for shade, drop in ((1, 1), (3, 0)):
        for i, ch in enumerate(label):
            ox = 1 + i * STEP[0] + drop + NUDGE.get(ch, 0)
            oy = 1 + i * STEP[1] + drop
            for y, row in enumerate(MICRO[ch]):
                for x, c in enumerate(row):
                    if c == '#':
                        px[oy + y][ox + x] = shade
    return px


def write_buttons(rom):
    for code, label in BUTTONS.items():
        glyphs.write_16(rom, BUTTON_FONT, code - 0x1FB, button(label))
    return len(BUTTONS)


# ----------------------------------------------------------- cursor skipping --
#
# Every blank cell in the chart is selectable, and the cursor is a palette swap
# on the cell it sits on, so on a blank one there is nothing to recolour and it
# simply vanishes. The English chart made that far worse than the Japanese one:
# forty-three of the 8x14 grid's cells are dead - four past the '9', fourteen in
# the empty row, and twenty-five around the three buttons.
#
# The game already skips its own blanks, in $82:A73D, which $82:A5A3 calls twice
# right after a move and before the cursor is redrawn. It is a hard-coded list -
# row 5 is empty, and rows 1 and 3 have a hole at column $0C - so it does not
# generalise. This replaces it with the same idea driven off the screen: read the
# glyph code under the cursor and, unless it is one the chart put there, keep
# stepping the way the d-pad was pushed. The chart is then the only thing
# deciding where the cursor can rest, and editing the `Name entry` sheet cannot
# strand it.
#
# What counts as somewhere to sit is a whitelist - a single letter, code $001 to
# $05E, or one of the three buttons - rather than "not blank". Row 5 is the
# reason: its entry in the chart string is empty, so nothing is ever written to
# those cells and what the text layer holds there is whatever the screen was
# cleared to. Testing for code $000 would be betting on that; testing for the
# codes the chart writes is not.
#
# $104E is the column, counted from the right - the screen cell is $1C - 2*col,
# because the kana chart read right to left - and $104F is the row, at row*2 +
# $0A. $02:BEE5 takes that position as (y << 8) | x and $02:C40A returns the code
# the text layer holds there, both exactly as $82:A681 uses them. The direction
# bits are the joypad's: $01 right, $02 left, $04 down, $08 up. $82:A511 has
# already dropped out of this path when none of them is set, so the walk always
# has a direction to follow.
#
# The step budget only exists so that a chart with a wholly blank row cannot hang
# the game: sixteen is twice the tallest wrap and past the widest.

CURSOR_CODE = 0x017600           # $02:F600, past battle_names' $02:F500
CURSOR_ORG = 0xF600
CURSOR_HOOKS = (0x0125A3, 0x0125A6)     # JSR $A73D, twice


def _cursor_code():
    out = bytearray()
    marks = {}

    def emit(*bs):
        out.extend(bs)

    def branch(op, name):
        emit(op, 0)
        marks.setdefault(name, []).append(len(out) - 1)

    def target(name):
        for at in marks.pop(name):
            out[at] = (len(out) - at - 1) & 0xFF

    def step(bit, mem, last):
        """One direction: the decrementing half wraps to `last`, the other to 0.

        Deliberately the same arithmetic as the move itself at $82:A52D-$A577,
        so a continued walk cannot drift from the step that started it.
        """
        lo, hi = mem & 0xFF, mem >> 8
        end = 'past%02x' % bit
        emit(0xA3, 0x01)                     # LDA $01,S    the direction bits
        emit(0x89, bit)                      # BIT #bit
        branch(0xF0, end)                    # BEQ past
        if bit in (0x01, 0x08):              # right / up
            emit(0xCE, lo, hi)               # DEC mem
            branch(0x10, end)                # BPL past
            emit(0xA9, last)                 # LDA #last
            emit(0x8D, lo, hi)               # STA mem
        else:                                # left / down
            emit(0xEE, lo, hi)               # INC mem
            emit(0xAD, lo, hi)               # LDA mem
            emit(0xC9, last + 1)             # CMP #last+1
            branch(0x90, end)                # BCC past
            emit(0x9C, lo, hi)               # STZ mem
        target(end)

    emit(0x08)                               # PHP
    emit(0xC2, 0x10)                         # REP #$10     X/Y 16-bit for C40A
    emit(0x5A)                               # PHY          under the direction
    emit(0xE2, 0x20)                         # SEP #$20     bits, so $01,S holds
    emit(0x48)                               # PHA          them all the way down
    emit(0xA0, 0x10, 0x00)                   # LDY #$0010   step budget
    top = len(out)
    emit(0xAD, 0x4F, 0x10)                   # LDA $104F    row
    emit(0x0A)                               # ASL
    emit(0x18)                               # CLC
    emit(0x69, 0x0A)                         # ADC #$0A     -> y cell
    emit(0xEB)                               # XBA
    emit(0xA9, 0x1C)                         # LDA #$1C
    emit(0x38)                               # SEC
    emit(0xED, 0x4E, 0x10)                   # SBC $104E
    emit(0xED, 0x4E, 0x10)                   # SBC $104E    -> x cell
    emit(0x22, 0xE5, 0xBE, 0x02)             # JSL $02BEE5  set the position
    emit(0x22, 0x0A, 0xC4, 0x02)             # JSL $02C40A  read the code
    # code - 1, so the two runs that count are 0..$5D and $204..$206
    emit(0xC2, 0x20)                         # REP #$20
    emit(0x38)                               # SEC
    emit(0xE9, 0x01, 0x00)                   # SBC #$0001
    emit(0xC9, 0x5E, 0x00)                   # CMP #$005E   a chart letter?
    branch(0x90, 'rest')                     # BCC rest
    emit(0xC9, 0x04, 0x02)                   # CMP #$0204
    branch(0x90, 'walk')                     # BCC walk
    emit(0xC9, 0x07, 0x02)                   # CMP #$0207   one of the buttons?
    branch(0xB0, 'walk')                     # BCS walk
    target('rest')
    emit(0xE2, 0x20)                         # SEP #$20
    branch(0x80, 'done')                     # BRA done     somewhere to sit
    target('walk')
    emit(0xE2, 0x20)                         # SEP #$20
    emit(0x88)                               # DEY
    branch(0xF0, 'done')                     # BEQ done     give up, never hang
    step(0x01, 0x104E, 0x0D)                 # right
    step(0x02, 0x104E, 0x0D)                 # left
    step(0x04, 0x104F, 0x07)                 # down
    step(0x08, 0x104F, 0x07)                 # up
    back = CURSOR_ORG + top
    emit(0x4C, back & 0xFF, back >> 8)       # JMP top
    target('done')
    emit(0x68)                               # PLA          direction bits back
    emit(0x7A)                               # PLY
    emit(0x28)                               # PLP
    emit(0x60)                               # RTS
    assert not marks, marks
    return bytes(out)


def cursor_patch(rom):
    code = _cursor_code()
    assert all(b == 0xFF for b in rom[CURSOR_CODE:CURSOR_CODE + len(code)]), \
        'cursor code space not free'
    rom[CURSOR_CODE:CURSOR_CODE + len(code)] = code
    for off in CURSOR_HOOKS:
        assert bytes(rom[off:off + 3]) == b'\x20\x3d\xa7', '%06X' % off
        rom[off + 1:off + 3] = CURSOR_ORG.to_bytes(2, 'little')
    return len(code)


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
    # the space / delete / end buttons, and a cursor that skips the blanks
    write_buttons(rom)
    return len(pairs), cursor_patch(rom)

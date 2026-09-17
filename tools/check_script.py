#!/usr/bin/env python3
"""Check the workbook before spending a build on it.

    python3 tools/check_script.py

Everything here is cheap and needs only the ROM and the workbook, so it is worth
running after every editing session. build.py enforces the byte budgets properly
once the dictionary has been fitted; this catches the mistakes that are easy to
make by hand and annoying to find later:

    tokens        every <...> in the English matches the Japanese, in order
    width         no line wider than the 14-cell box it is drawn in, even
                  when a number field holds five digits
    ASCII         no curly quotes, em dashes, ellipsis characters or accents
    ratio         English far enough under budget that the dictionary can cope

The ratio check is a warning, not an error - accepted strings run from 0.4x to
2.5x their byte budget and only the dictionary fit can say for certain.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
import wmtool
import sheet

TOK = re.compile(r'<[^>]*>')
CELLS = 14                # a dialogue box or description panel, in cells
RATIO = 2.6


def cells(line, digits=1):
    """Cell width of one line, the way $90:9605 actually lays it out.

    A half-width ASCII glyph is half a cell. Everything else is a whole one - a
    full-width space, a window frame tile, a $1F icon - and a <NAME> field is
    as wide as the value it prints, with its declared width the floor.

    The part that is easy to miss, and that counting characters cannot express:
    a whole-cell glyph will not share a cell. RENDER's static path closes any
    half-open cell and steps past it before writing, and the <NAME> field does
    the same in NEWARG. So a frame tile after an odd run of letters costs an
    extra half cell - which is how " 50 Bezetta<EE9><EE9> " and six blanks came
    to fifteen cells in a fourteen-cell window and ate the right border.

    A number field is measured holding `digits` digits. NUMPAD right-aligns it
    in its declared width - whole blank cells, then a half blank when the digit
    count is odd - as long as it fits. A number that outgrows its field just
    flows as half-width text: three or more digits in a <NUM7:vv01>.
    """
    n, half, i = 0.0, False, 0

    def close():
        nonlocal n, half
        if half:
            n += 0.5
            half = False

    while i < len(line):
        c = line[i]
        if c == '<':
            j = line.index('>', i)
            body = line[i + 1:j]
            i = j + 1
            if body[0] in 'ES':              # frame tile or icon: a whole cell
                close()
                n += 1.0
            elif body[0] == 'G':             # a manufactured half-width glyph
                n += 0.5
                half = not half
            elif body.startswith('NAME:'):
                close()
                n += int(body.split(':')[1][2:], 16)
            elif body.startswith(('NUM7:', 'NUM8:')):
                width = int(body.split(':')[1][2:], 16)
                if width - (digits + 1) // 2 >= 0:
                    close()
                    n += width
                else:
                    n += digits * 0.5
                    half ^= bool(digits & 1)
            continue
        i += 1
        if c == '\n':
            continue
        if c == '　' or ord(c) > 0x2000:
            close()
            n += 1.0
        else:
            n += 0.5
            half = not half
    close()                                  # the newline closes the last cell
    return n


DIGITS = 5                # the most a 16-bit value prints

# offsets whose layout is columns, not prose - width is checked by build.py
SKIP_WIDTH = range(0x090000, 0x090EF6)


def main():
    text = sheet.text()
    errors = warnings = 0
    for off, en in sorted(text.items()):
        toks, end = wmtool.decode(off)
        jp = wmtool.text(toks).rstrip('\n')
        budget = end - off

        want, got = TOK.findall(jp), TOK.findall(en)
        if want != got:
            print('$%06X tokens differ\n    Japanese %s\n    English  %s'
                  % (off, want, got))
            errors += 1

        if off not in SKIP_WIDTH:
            for line in en.split('\n'):
                # Cells, not characters. A full-width space is one whole
                # cell - two half-width characters - and so is a frame
                # glyph or an icon, so counting characters under-reads any
                # line carrying one. The panel is fourteen cells; a line at
                # 14.5 puts its last glyph, usually the full stop, on the
                # border.
                w = cells(line)
                if w > CELLS:
                    print('$%06X line is %s cells, window is %d: %r'
                          % (off, w, CELLS, line))
                    errors += 1
                elif cells(line, DIGITS) > CELLS:
                    # Experience from the Ilion fight is five digits, and a
                    # field that grew past the window ate the border.
                    print('$%06X line reaches %s cells with a five-digit number,'
                          ' window is %d: %r'
                          % (off, cells(line, DIGITS), CELLS, line))
                    errors += 1

        bad = [c for c in en if ord(c) > 0x7E and c != '\u3000']
        if bad:
            print('$%06X non-ASCII: %s' % (off, ' '.join(sorted(set(bad)))))
            errors += 1

        n = len(TOK.sub('', en).replace('\u3000', ''))
        if budget and n / budget > RATIO:
            print('$%06X %.2fx budget (%d chars in %d bytes) - may not fit'
                  % (off, n / budget, n, budget))
            warnings += 1

    print('%d strings checked, %d errors, %d warnings' % (len(text), errors, warnings))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())

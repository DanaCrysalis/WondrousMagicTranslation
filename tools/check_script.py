#!/usr/bin/env python3
"""Check the workbook before spending a build on it.

    python3 tools/check_script.py

Everything here is cheap and needs only the ROM and the workbook, so it is worth
running after every editing session. build.py enforces the byte budgets properly
once the dictionary has been fitted; this catches the mistakes that are easy to
make by hand and annoying to find later:

    tokens        every <...> in the English matches the Japanese, in order
    width         no line wider than the 14-cell box it is drawn in
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


def cells(line):
    """Cell width of one line: a half-width ASCII glyph is half a cell.

    Everything else is a whole one - a full-width space, a window frame
    tile, a $1F icon - and a <NAME> or <NUM> field is as wide as the value
    it prints, with its declared width as the floor. Counting characters
    instead misses both directions at once.
    """
    n, i = 0.0, 0
    while i < len(line):
        c = line[i]
        if c == '<':
            j = line.index('>', i)
            body = line[i + 1:j]
            i = j + 1
            if body[0] in 'ES':
                n += 1.0
            elif body[0] == 'G':
                n += 0.5
            elif body.startswith(('NAME:', 'NUM7:', 'NUM8:')):
                n += int(body.split(':')[1][2:], 16)
            continue
        i += 1
        if c != '\n':
            n += 1.0 if (c == '\u3000' or ord(c) > 0x2000) else 0.5
    return n

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

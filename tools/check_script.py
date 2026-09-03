#!/usr/bin/env python3
"""Check the workbook before spending a build on it.

    python3 tools/check_script.py

Everything here is cheap and needs only the ROM and the workbook, so it is worth
running after every editing session. build.py enforces the byte budgets properly
once the dictionary has been fitted; this catches the mistakes that are easy to
make by hand and annoying to find later:

    tokens        every <...> in the English matches the Japanese, in order
    width         no line over 28 half-width characters in a dialogue box
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
WIDTH = 28
RATIO = 2.6

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
            for line in TOK.sub('', en).split('\n'):
                if len(line) > WIDTH:
                    print('$%06X line is %d wide: %r' % (off, len(line), line))
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

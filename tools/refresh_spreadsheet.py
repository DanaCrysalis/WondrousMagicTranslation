#!/usr/bin/env python3
"""Refresh the ROM-derived columns of data/Wondrous_Magic_script.ods.

    python3 tools/refresh_spreadsheet.py

The workbook is the script; this tool must never invent English.

What it rewrites, from the ROM:

    ID, Block, ROM, CPU, Bytes, Japanese, Raw hex     every Script row
    English                                           block A rows only

What it carries across untouched:

    English for blocks B and C, and the Status column
    Item names, Descriptions, Monster names, Title screen, Name entry,
    Intro crawl, Glossary, Questions, Control codes, Read me

Block A English is generated, not authored - the descriptions are assembled from
the `Item names` and `Descriptions` sheets plus the icon run in the original ROM
string. Those cells are shaded grey to say so. Edit the two source sheets, not
the Script sheet.

Rows are matched by ROM offset, so re-running after a block boundary changes
keeps every translation attached to the right string.

ODS is edited by rebuilding rather than by poking at cells, so this writes the
whole document each time. Sheets it does not generate are read and re-emitted,
so nothing is lost - but this is the only writer, so a sheet added by hand needs
a line in SHEETS below or it comes back with the plain default styling.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
import wmtool
import sheet
import book

HEAD = '1F3864'          # header row
EDIT = 'FFF9D6'          # authored: type here
DONE = 'E7F3E7'          # authored and marked done
GEN = 'F0F0F0'           # generated from elsewhere, do not edit

HDR = ['ID', 'Block', 'ROM', 'CPU', 'Bytes', 'Status', 'Japanese', 'English',
       'EN bytes', 'Raw hex']
WIDTH = [9, 6, 10, 11, 7, 8, 46, 46, 9, 46]

# name -> (column widths, index of the authored column or None)
# LENCOL adds a live character count: sheet -> (column to write, column to count)
SHEETS = {
    'Read me':       ([34, 60], None),
    'Item names':    ([20, 20], 1),
    'Descriptions':  ([54, 54], 1),
    'Monster names': ([7, 11, 16, 18, 7], 3),
    'Title screen':  ([11, 40], 1),
    'Name entry':    ([7, 34, 9], 1),
    'Intro crawl':   ([11, 7, 54, 8], 2),
    'Glossary':      ([20, 20, 14, 40], 1),
    'Questions':     ([18, 44, 44, 10], None),
    'Control codes': ([8, 14, 10, 44], None),
}
LENCOL = {'Monster names': (4, 3)}
ORDER = ['Read me', 'Script', 'Item names', 'Descriptions', 'Monster names',
         'Title screen', 'Name entry', 'Intro crawl', 'Glossary', 'Questions',
         'Control codes']


def script_rows(existing):
    """Rebuild every Script row from the ROM, keeping the authored English."""
    kept = {}
    for row in existing[1:]:
        rom = book.cell([row], 0, 2)
        if rom:
            kept[int(str(rom).lstrip('$'), 16)] = book.cell([row], 0, 7)
    generated, missing = sheet.block_a()
    if missing:
        print('block A: %d strings have no English yet' % len(missing))
    rows = []
    for blk, a, b in wmtool.TEXT_BLOCKS:
        p, n = a, 0
        while p < b:
            toks, q = wmtool.decode(p)
            bank, addr = wmtool.pc2snes(p)
            en = generated.get(p, '') if blk == 'A' else (kept.get(p) or '')
            rows.append(['%s%04d' % (blk, n), blk, '$%06X' % p,
                         '$%02X:%04X' % (bank, addr), q - p,
                         'done' if en else '',
                         wmtool.text(toks).rstrip('\n'), en,
                         None, wmtool.ROM[p:q].hex().upper()])
            p, n = q, n + 1
    return rows


def write(path, sheets):
    """Emit the whole workbook. `sheets` is {name: rows}, Script included."""
    w = book.Writer()
    head = w.cellstyle(fill=HEAD, bold=True, colour='FFFFFF')
    plain = w.cellstyle(top=True)
    wrapped = w.cellstyle(wrap=True, top=True)
    jp = w.cellstyle(size=11, wrap=True, top=True)
    raw = w.cellstyle(font='Courier New', size=8, colour='808080', top=True)
    gen = w.cellstyle(fill=GEN, wrap=True, top=True)
    done = w.cellstyle(fill=DONE, wrap=True, top=True)
    edit = w.cellstyle(fill=EDIT, wrap=True, top=True)

    for name in ORDER + [n for n in sheets if n not in ORDER]:
        rows = sheets.get(name)
        if rows is None:
            continue
        if name == 'Script':
            t = w.sheet(name, WIDTH)
            w.row(t, HDR, [head] * len(HDR))
            for i, row in enumerate(rows[1:], start=2):
                styles = [plain] * 10
                styles[6], styles[9] = jp, raw
                styles[7] = gen if row[1] == 'A' else (done if row[5] else edit)
                tr = w.row(t, row[:8] + [None] + row[9:], styles)
                # the placeholder becomes a live length, with its value cached
                # so a workbook that has never been opened still reads right
                cell = w.formula('IF([.H%d]="";"";LEN([.H%d]))' % (i, i),
                                 len(row[7] or ''), plain)
                tr.insertBefore(cell, tr.childNodes[8])
                tr.removeChild(tr.childNodes[9])
        else:
            widths, encol = SHEETS.get(name, ([24] * 8, None))
            t = w.sheet(name, widths, freeze_header=(name != 'Read me'))
            for i, row in enumerate(rows):
                if i == 0 and name != 'Read me':
                    w.row(t, row, [head] * len(row))
                    continue
                lc = LENCOL.get(name)
                if lc:
                    row = list(row) + [None] * (lc[0] + 1 - len(row))
                    row[lc[0]] = None
                styles = [wrapped] * max(len(row), 1)
                if encol is not None and encol < len(styles):
                    styles[encol] = edit
                tr = w.row(t, row, styles)
                if lc:
                    col = chr(ord('A') + lc[1])
                    cell = w.formula('LEN([.%s%d])' % (col, i + 1),
                                     len(str(row[lc[1]] or '')), plain)
                    tr.insertBefore(cell, tr.childNodes[lc[0]])
                    tr.removeChild(tr.childNodes[lc[0] + 1])
    w.save(path)


def main():
    path = os.path.join(paths.DATA, 'Wondrous_Magic_script.ods')
    sheets = book.read(path)
    sheets['Script'] = [HDR] + script_rows(sheets.get('Script', [HDR]))
    rows = sheets['Script'][1:]
    n = len(rows)
    d = sum(1 for r in rows if r[5])
    for r in sheets.get('Read me', []):
        if r and r[0] in ('Strings', 'Translated', 'Remaining'):
            r[1] = {'Strings': n, 'Translated': d, 'Remaining': n - d}[r[0]]
    write(path, sheets)
    print('%s: %d strings, %d translated, %d remaining'
          % (os.path.basename(path), n, d, n - d))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Refresh the ROM-derived columns of data/Wondrous_Magic_script.xlsx in place.

    python3 tools/refresh_spreadsheet.py

This replaces the old make_spreadsheet.py, and it works the other way round.
The workbook used to be generated from the script_*.py modules; now the workbook
is the script and there are no modules. So this tool must never invent English.

What it rewrites, from the ROM:

    ID, Block, ROM, CPU, Bytes, Japanese, Raw hex     every Script row
    English                                           block A rows only

What it leaves completely alone:

    English for blocks B and C, and the Status column
    Item names, Descriptions, Title screen, Name entry, Intro crawl
    Glossary, Questions

Block A English is generated, not authored - the descriptions are assembled from
the `Item names` and `Descriptions` sheets plus the icon run in the original ROM
string. Those cells are shaded grey to say so. Edit the two source sheets, not
the Script sheet.

Rows are matched by ROM offset, so re-running after a block boundary changes
keeps every translation attached to the right string.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
import wmtool
import sheet
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

HEAD = PatternFill('solid', fgColor='1F3864')
EDIT = PatternFill('solid', fgColor='FFF9D6')
DONE = PatternFill('solid', fgColor='E7F3E7')
GEN = PatternFill('solid', fgColor='F0F0F0')
THIN = Side(style='thin', color='D0D0D0')

HDR = ['ID', 'Block', 'ROM', 'CPU', 'Bytes', 'Status', 'Japanese', 'English',
       'EN bytes', 'Raw hex']


def main():
    import openpyxl
    book = os.path.join(paths.DATA, 'Wondrous_Magic_script.xlsx')
    wb = openpyxl.load_workbook(book)
    ws = wb['Script']

    # keep what the humans wrote, keyed by offset rather than by row
    kept = {}
    for r in range(2, ws.max_row + 1):
        rom = ws.cell(r, 3).value
        if rom:
            kept[int(str(rom).lstrip('$'), 16)] = (ws.cell(r, 8).value,
                                                   ws.cell(r, 6).value)

    generated, missing = sheet.block_a()
    if missing:
        print('block A: %d strings have no English yet' % len(missing))

    rows = []
    for blk, a, b in wmtool.TEXT_BLOCKS:
        p, n = a, 0
        while p < b:
            toks, q = wmtool.decode(p)
            bank, addr = wmtool.pc2snes(p)
            if blk == 'A':
                en = generated.get(p, '')
            else:
                en = kept.get(p, ('', ''))[0] or ''
            rows.append(['%s%04d' % (blk, n), blk, '$%06X' % p,
                         '$%02X:%04X' % (bank, addr), q - p,
                         'done' if en else '',
                         wmtool.text(toks).rstrip('\n'), en,
                         None, wmtool.ROM[p:q].hex().upper()])
            p, n = q, n + 1

    ws.delete_rows(1, ws.max_row)
    ws.append(HDR)
    for row in rows:
        ws.append(row)
    for r in range(2, len(rows) + 2):
        ws.cell(r, 9).value = '=IF(H%d="","",LEN(H%d))' % (r, r)

    for c in range(1, len(HDR) + 1):
        cell = ws.cell(1, c)
        cell.font = Font(name='Arial', size=10, bold=True, color='FFFFFF')
        cell.fill = HEAD
        cell.alignment = Alignment(horizontal='center', vertical='center')
    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = 'A1:J%d' % (len(rows) + 1)
    for k, v in {'A': 9, 'B': 6, 'C': 10, 'D': 11, 'E': 7, 'F': 8,
                 'G': 46, 'H': 46, 'I': 9, 'J': 46}.items():
        ws.column_dimensions[k].width = v
    for r in range(2, len(rows) + 2):
        for c in range(1, len(HDR) + 1):
            cell = ws.cell(r, c)
            cell.font = Font(name='Arial', size=10)
            cell.border = Border(bottom=THIN)
            cell.alignment = Alignment(vertical='top', wrap_text=(c in (7, 8)))
        ws.cell(r, 7).font = Font(name='Arial', size=11)
        ws.cell(r, 10).font = Font(name='Courier New', size=8, color='808080')
        if ws.cell(r, 2).value == 'A':
            ws.cell(r, 8).fill = GEN            # generated, do not edit here
        else:
            ws.cell(r, 8).fill = DONE if ws.cell(r, 6).value else EDIT

    done = sum(1 for r in rows if r[5])
    lg = wb['Read me']
    for r in range(1, lg.max_row + 1):
        if lg.cell(r, 1).value == 'Strings':
            lg.cell(r, 2).value = len(rows)
        if lg.cell(r, 1).value == 'Translated':
            lg.cell(r, 2).value = done
        if lg.cell(r, 1).value == 'Remaining':
            lg.cell(r, 2).value = len(rows) - done

    wb.save(book)
    print('%s: %d strings, %d translated, %d remaining'
          % (os.path.basename(book), len(rows), done, len(rows) - done))


if __name__ == '__main__':
    main()

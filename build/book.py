#!/usr/bin/env python3
"""The workbook, in OpenDocument.

`data/Wondrous_Magic_script.ods`. It was .xlsx; it is .ods because that is what
the person authoring the script can save, and the format was never doing any
work beyond holding rows of text.

Only two things touch the workbook - `build/sheet.py` reads it and
`tools/refresh_spreadsheet.py` rewrites the ROM-derived columns of the Script
sheet - so rather than pull in a general spreadsheet library this is the small
piece of ODS both of them need.

    read(path)              {sheet name: [[cell, ...], ...]}
    Writer                  build a whole workbook and save it

Cells come back as str, int, float or None. Formula cells give their last
cached value, which is what LibreOffice stores alongside the formula, so a
sheet that has never been opened still reads correctly as long as whatever
wrote it filled the value in.

odfpy is the one dependency, and it is pure Python:

    pip install odfpy
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from odf.opendocument import OpenDocumentSpreadsheet, load
    from odf.table import (Table, TableRow, TableCell, TableColumn,
                           TableHeaderRows)
    from odf.text import P
    from odf.style import (Style, TextProperties, TableColumnProperties,
                           TableCellProperties, ParagraphProperties)
    from odf.config import (ConfigItemSet, ConfigItem, ConfigItemMapEntry,
                            ConfigItemMapNamed, ConfigItemMapIndexed)
except ImportError:
    raise SystemExit('the workbook is OpenDocument now: pip install odfpy')

CELL = 'urn:oasis:names:tc:opendocument:xmlns:table:1.0'
OFF = 'urn:oasis:names:tc:opendocument:xmlns:office:1.0'


# ------------------------------------------------------------------ read ----

def _cell_value(cell):
    kind = cell.getAttrNS(OFF, 'value-type')
    if kind in ('float', 'percentage', 'currency'):
        v = float(cell.getAttrNS(OFF, 'value'))
        return int(v) if v == int(v) else v
    if kind == 'boolean':
        return cell.getAttrNS(OFF, 'boolean-value') == 'true'
    if kind is None:
        return None
    # string and date: the displayed paragraphs, one per line
    lines = [str(p) for p in cell.getElementsByType(P)]
    text = '\n'.join(lines)
    return text if text != '' else None


def _rows(table):
    out = []
    for row in table.getElementsByType(TableRow):
        rep = int(row.getAttrNS(CELL, 'number-rows-repeated') or 1)
        cells = []
        for cell in row.getElementsByType(TableCell):
            n = int(cell.getAttrNS(CELL, 'number-columns-repeated') or 1)
            v = _cell_value(cell)
            if n > 512 and v is None:
                break                      # the trailing run to column 1024
            cells.extend([v] * n)
        while cells and cells[-1] is None:
            cells.pop()
        if rep > 512 and not cells:
            break                          # the trailing run of empty rows
        out.extend([list(cells) for _ in range(rep)])
    while out and not out[-1]:
        out.pop()
    return out


def read(path):
    """{sheet name: rows}, rows being lists of cells, ragged and trimmed."""
    if not os.path.exists(path):
        raise SystemExit('missing %s' % path)
    doc = load(path)
    return {t.getAttrNS(CELL, 'name'): _rows(t)
            for t in doc.spreadsheet.getElementsByType(Table)}


def cell(rows, r, c):
    """rows[r][c] with the ragged edges treated as empty. 0-based."""
    if r < len(rows) and c < len(rows[r]):
        return rows[r][c]
    return None


# ----------------------------------------------------------------- write ----

class Writer:
    """A whole workbook, built sheet by sheet and saved once.

    Styling is deliberately thin - a background colour, a font, and wrapping is
    all the workbook ever used it for. Widths are in centimetres because that is
    what ODS stores; `width` takes the old character counts and converts, so the
    numbers in refresh_spreadsheet.py did not have to be re-tuned.
    """

    def __init__(self):
        self.doc = OpenDocumentSpreadsheet()
        self._styles = {}
        self._cols = {}
        self._freeze = {}
        self.tables = []

    # -- styles
    def _style(self, family, key, build):
        if key not in self._styles:
            s = Style(name='s%d' % len(self._styles), family=family)
            build(s)
            self.doc.automaticstyles.addElement(s)
            self._styles[key] = s
        return self._styles[key]

    def cellstyle(self, fill=None, font='Arial', size=10, bold=False,
                  colour=None, wrap=False, top=False):
        key = ('cell', fill, font, size, bold, colour, wrap, top)

        def build(s):
            if fill:
                s.addElement(TableCellProperties(backgroundcolor='#' + fill))
            s.addElement(TableCellProperties(
                wrapoption='wrap' if wrap else 'no-wrap',
                verticalalign='top' if top else 'middle'))
            s.addElement(TextProperties(
                fontname=font, fontsize='%dpt' % size,
                fontweight='bold' if bold else 'normal',
                color='#' + colour if colour else '#000000'))
        return self._style('table-cell', key, build)

    def _colstyle(self, chars):
        def build(s):
            s.addElement(TableColumnProperties(columnwidth='%.2fcm'
                                               % (chars * 0.21 + 0.2)))
        return self._style('table-column', ('col', chars), build)

    # -- content
    def sheet(self, name, widths=(), freeze_header=True):
        t = Table(name=name)
        for w in widths:
            t.addElement(TableColumn(stylename=self._colstyle(w)))
        self.doc.spreadsheet.addElement(t)
        self.tables.append(name)
        self._freeze[name] = freeze_header
        return t

    def row(self, table, values, styles=None):
        tr = TableRow()
        table.addElement(tr)
        for i, v in enumerate(values):
            st = styles[i] if styles and i < len(styles) else None
            tr.addElement(self._cell(v, st))
        return tr

    def _cell(self, v, style):
        kw = {'stylename': style} if style is not None else {}
        if v is None or v == '':
            return TableCell(**kw)
        if isinstance(v, bool):
            return TableCell(valuetype='boolean', booleanvalue=v, **kw)
        if isinstance(v, (int, float)):
            c = TableCell(valuetype='float', value=v, **kw)
            c.addElement(P(text=str(v)))
            return c
        c = TableCell(valuetype='string', **kw)
        for line in str(v).split('\n'):
            c.addElement(P(text=line))
        return c

    def formula(self, expr, cached, style=None):
        """A cell carrying a formula and the value it currently evaluates to.

        The cached value matters: sheet.py reads values, and a workbook written
        here and never opened in LibreOffice would otherwise read as blank.
        """
        kw = {'stylename': style} if style is not None else {}
        c = TableCell(formula='of:=' + expr, valuetype='float',
                      value=cached, **kw)
        c.addElement(P(text=str(cached)))
        return c

    # -- save
    def save(self, path):
        self._write_settings()
        self.doc.save(path)

    def _write_settings(self):
        """Freeze the header row of every sheet that asked for it.

        Panes live in settings.xml, not content.xml, and a 900-row sheet with
        the header scrolled off is unusable, so it is worth the ceremony.
        """
        views = ConfigItemMapEntry()
        tables = ConfigItemMapNamed(name='Tables')
        for name in self.tables:
            e = ConfigItemMapEntry(name=name)
            if self._freeze[name]:
                for k, v in (('HorizontalSplitMode', 0), ('VerticalSplitMode', 2),
                             ('HorizontalSplitPosition', 0), ('VerticalSplitPosition', 1),
                             ('PositionTop', 1), ('PositionBottom', 1)):
                    item = ConfigItem(name=k, type='short' if 'Mode' in k else 'int')
                    item.addText(str(v))
                    e.addElement(item)
            tables.addElement(e)
        views.addElement(tables)
        active = ConfigItem(name='ActiveTable', type='string')
        active.addText(self.tables[0])
        views.addElement(active)
        idx = ConfigItemMapIndexed(name='Views')
        idx.addElement(views)
        s = ConfigItemSet(name='ooo:view-settings')
        s.addElement(idx)
        self.doc.settings.addElement(s)

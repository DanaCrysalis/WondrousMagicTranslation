#!/usr/bin/env python3
"""The workbook is the script.

`data/Wondrous_Magic_script.xlsx` is now the only place English is authored.
This module reads it and hands the build the same shapes the old script_a.py,
script_b.py, script_c.py and the systext/prologue tables used to hand it:

    text()          {rom offset: English} for blocks A, B and C
    title()         {rom offset: English} for the title and save screens
    chart()         [str] the name entry grid, one string per row
    crawl()         ([str], [str]) the intro poem and the prologue

Blocks B and C are authored directly in the Script sheet: what is in the English
column is what gets inserted. Block A is not. Its 150-odd descriptions are still
assembled from three pieces - the English name, the icon run copied out of the
original ROM string, and the description body - because the icon run has to be
carried over verbatim and the name has to be padded to the width the Japanese
name occupied. So block A is authored on the `Item names` and `Descriptions`
sheets, and its English column in `Script` is generated. Editing it there does
nothing; `tools/refresh_spreadsheet.py` overwrites it.

Everything is read once and cached. openpyxl is required at build time now.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
import wmtool

BOOK = os.path.join(paths.DATA, 'Wondrous_Magic_script.xlsx')

BLOCK_A = (0x0912C0, 0x092FE0)

_cache = {}


def _book():
    if 'wb' not in _cache:
        try:
            import openpyxl
        except ImportError:
            raise SystemExit('the build reads the workbook now: pip install openpyxl')
        if not os.path.exists(BOOK):
            raise SystemExit('missing %s' % BOOK)
        _cache['wb'] = openpyxl.load_workbook(BOOK, data_only=True)
    return _cache['wb']


def _rows(name, first=2):
    ws = _book()[name]
    for r in range(first, ws.max_row + 1):
        yield [ws.cell(r, c).value for c in range(1, ws.max_column + 1)]


# ---------------------------------------------------------------- block A ----

def names():
    """{Japanese item name: English}."""
    if 'names' not in _cache:
        _cache['names'] = {jp: en for jp, en, *_ in _rows('Item names')
                           if jp is not None and en is not None}
    return _cache['names']


def bodies():
    """{Japanese description body: English}."""
    if 'bodies' not in _cache:
        _cache['bodies'] = {jp: en for jp, en, *_ in _rows('Descriptions')
                            if jp is not None and en is not None}
    return _cache['bodies']


def block_a():
    """Walk block A and assemble {offset: English}, plus a list of misses.

    Lifted unchanged from the old script_a.build(); only the two tables moved.
    """
    NAMES, TAILS = names(), bodies()
    out, missing = {}, []
    p, end = BLOCK_A
    while p < end:
        toks, q = wmtool.decode(p)
        s = wmtool.text(toks).rstrip('\n')
        if not any(ord(c) > 0x2000 for c in s):
            p = q
            continue
        if '\n' not in s:
            if s in NAMES:
                out[p] = NAMES[s]
            else:
                missing.append((p, s))
            p = q
            continue
        head, _, tail = s.partition('\n')
        tail = '\n' + tail
        i = head.find('<S')
        jp_name, icons = (head[:i], head[i:]) if i >= 0 else (head, '')
        en_name = NAMES.get(jp_name.rstrip())
        en_tail = TAILS.get(tail.lstrip('\n') and tail[1:])
        if en_name is None or en_tail is None:
            missing.append((p, s))
            p = q
            continue
        # every rendered Japanese glyph is one whole cell, so the name and its
        # padding are worth twice as many half-width slots. Where an English
        # name will not fit that, the icon run simply shifts left - it only has
        # to stay inside the 14-cell window.
        icons = icons.replace('＋', '+').replace('−', '-').replace('？', '?')
        pad = max(1, 2 * len(re.sub(r'<[^>]*>', '', jp_name)) - len(en_name))
        line = en_name + ' ' * pad + icons
        width = len(re.sub(r'<[^>]*>', '', line)) * 0.5 + line.count('<S')
        if width > 14:
            missing.append((p, 'first line %s cells: %s' % (width, en_name)))
            p = q
            continue
        out[p] = line + '\n' + en_tail
        p = q
    return out, missing


# ------------------------------------------------------------ blocks B, C ----

def authored():
    """{offset: English} for every Script row with English, block A excluded."""
    if 'authored' not in _cache:
        out = {}
        for row in _rows('Script'):
            rom, en = row[2], row[7]
            if not rom or en in (None, ''):
                continue
            off = int(str(rom).lstrip('$'), 16)
            if BLOCK_A[0] <= off < BLOCK_A[1]:
                continue                      # generated, see block_a()
            out[off] = en
        _cache['authored'] = out
    return _cache['authored']


def text():
    """{offset: English} for blocks A, B and C together."""
    if 'text' not in _cache:
        a, missing = block_a()
        if missing:
            raise SystemExit('block A: %d unmatched, first %r' % (len(missing), missing[:3]))
        out = dict(a)
        out.update(authored())
        _cache['text'] = out
    return _cache['text']


# ------------------------------------------------------- title and crawl ----

def title():
    """{offset: English} for the title screen and save menus."""
    if 'title' not in _cache:
        _cache['title'] = {int(str(rom).lstrip('$'), 16): en
                           for rom, en, *_ in _rows('Title screen')
                           if rom and en is not None}
    return _cache['title']


def chart():
    """The name entry grid, one string per row, in order."""
    if 'chart' not in _cache:
        rows = [(int(n), '' if cells is None else str(cells))
                for n, cells, *_ in _rows('Name entry') if n is not None]
        _cache['chart'] = [c for _, c in sorted(rows)]
    return _cache['chart']


def crawl():
    """(poem, prologue) as lists of lines, in order."""
    if 'crawl' not in _cache:
        got = {'POEM': [], 'PROLOGUE': []}
        for section, n, t, *_ in _rows('Intro crawl'):
            if section in got and n is not None:
                got[section].append((int(n), '' if t is None else str(t)))
        _cache['crawl'] = tuple([t for _, t in sorted(v)] for v in
                                (got['POEM'], got['PROLOGUE']))
    return _cache['crawl']


if __name__ == '__main__':
    t = text()
    poem, prologue = crawl()
    print('%s\n  blocks A+B+C  %d strings\n  title screen  %d\n'
          '  name entry    %d rows\n  intro crawl   %d + %d lines'
          % (os.path.basename(BOOK), len(t), len(title()),
             len(chart()), len(poem), len(prologue)))

#!/usr/bin/env python3
"""Dictionary compression for the script.

`$0E nn` prints dictionary entry nn by re-entering the interpreter, so a common
word costs two bytes however long it is. Without this English does not fit:
Japanese kana carry a whole syllable per byte, so a literal translation is
routinely two or three times the original size.

Layout, in free ROM:

    $3E:A000   256 x uint16 pointer table   (ROM $1F2000)
    $3E:A200   entries, each $00 terminated (ROM $1F2200)

Entries are plain text - no tokens, no nesting - so they encode with
`wmtool.encode_en` directly.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
import wmtool
import re

TABLE = 0x1F2000          # $3E:A000, 512 x uint16
ENTRIES = 0x1F2600        # $3E:A600
LIMIT = 0x1F8000
BANK1 = 254               # slots 0-253 cost two bytes; 254 and 255 are escapes
MAX_ENTRIES = 765         # 256-511 via $FF, 512-767 via $FE, both three bytes


def slot(i):
    """List index to table slot, stepping over the two escape markers."""
    return i if i < BANK1 else i + 2

TOKEN = re.compile(r'<[^>]*>|\n')


def _plain_runs(text):
    """The stretches of a string that can carry dictionary references."""
    out, last = [], 0
    for m in TOKEN.finditer(text):
        if m.start() > last:
            out.append(text[last:m.start()])
        last = m.end()
    if last < len(text):
        out.append(text[last:])
    return out


def choose(texts, count=MAX_ENTRIES, lo=3, hi=24):
    """Greedy: repeatedly take the substring that saves the most bytes."""
    runs = [r for t in texts for r in _plain_runs(t)]
    chosen = []
    for _ in range(count):
        gain = {}
        for r in runs:
            n = len(r)
            for i in range(n):
                for L in range(lo, min(hi, n - i) + 1):
                    s = r[i:i+L]
                    gain[s] = gain.get(s, 0) + (L - 2)
        best, score = None, 0
        for s, g in gain.items():
            g -= len(s) + 1                      # the entry costs its own bytes
            if g > score:
                best, score = s, g
        if best is None:
            break
        chosen.append(best)
        runs = [seg for r in runs for seg in r.split(best) if seg]
    return chosen


def _grow(texts_budgets, entries):
    """Force extra entries until every string fits. A string that will not fit
    any other way gets its own entry and then costs three bytes: $1E nn $00.
    This is how the short ones - names, places, spells - come in under budget."""
    entries = list(entries)
    for _ in range(MAX_ENTRIES):
        over = [(t, b) for t, b in texts_budgets if len(encode(t, entries)) > b]
        if not over:
            break
        t, _ = max(over, key=lambda tb: len(encode(tb[0], entries)) - tb[1])
        runs = [r for r in _plain_runs(t) if r not in entries and len(r) >= 3]
        if not runs or len(entries) >= MAX_ENTRIES:
            break
        # front of the list, so a forced entry always lands in the cheap bank -
        # the strings that need one are the ones with no budget to spare
        entries.insert(0, max(runs, key=len))
    return entries


def fit(texts_budgets, entries):
    """Grow, then rank, then check again. Ranking moves entries between banks,
    which can push a string that fitted back over, so it takes a few passes."""
    entries = list(entries)
    for _ in range(6):
        entries = reorder(texts_budgets, _grow(texts_budgets, entries))
        if not any(len(encode(t, entries)) > b for t, b in texts_budgets):
            break
    return entries


def reorder(texts_budgets, entries):
    """Put the entries the tightest strings depend on into the cheap bank.

    A three-byte budget can only afford a two-byte reference, so an entry that
    such a string needs must land below slot 254. Rank every entry by the
    smallest budget that references it."""
    need = {e: 10 ** 6 for e in entries}
    for t, b in texts_budgets:
        for e in entries:
            if e in t:
                need[e] = min(need[e], b)
    return sorted(entries, key=lambda e: (need[e], -len(e)))


def encode(text, entries):
    """Longest match first; falls back to literal bytes."""
    order = sorted(range(len(entries)), key=lambda i: -len(entries[i]))
    out = bytearray()
    i = 0
    while i < len(text):
        if text[i] == '<':
            j = text.index('>', i) + 1
            out += wmtool.encode_en(text[i:j])[:-1]
            i = j
            continue
        if text[i] == '\n':
            out.append(0x0D); i += 1; continue
        for k in order:
            e = entries[k]
            if text.startswith(e, i):
                sl = slot(k)
                if sl < BANK1:
                    out += bytes([0x0E, sl])
                elif sl < 512:
                    out += bytes([0x0E, 0xFF, sl - 256])
                else:
                    out += bytes([0x0E, 0xFE, sl - 512])
                i += len(e); break
        else:
            out += wmtool.encode_en(text[i])[:-1]
            i += 1
    out.append(0x00)
    return bytes(out)


def write(rom, entries):
    assert len(entries) <= MAX_ENTRIES
    off = ENTRIES
    ptrs = [0xA600] * 768
    for i, e in enumerate(entries):
        ptrs[slot(i)] = 0x8000 + (off - 0x1F0000)
        data = wmtool.encode_en(e)
        rom[off:off + len(data)] = data
        off += len(data)
    assert off < LIMIT, 'dictionary overflows free space'
    rom[TABLE:TABLE + 1536] = b''.join(p.to_bytes(2, 'little') for p in ptrs)
    return off - ENTRIES

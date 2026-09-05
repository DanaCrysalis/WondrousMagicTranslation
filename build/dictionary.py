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
import re, time

VERBOSE = os.environ.get('WM_VERBOSE')


def _say(msg):
    if VERBOSE:
        print('    %7.1fs  %s' % (time.time() - _T0, msg), flush=True)

_T0 = time.time()

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
    for _n in range(count):
        if _n % 25 == 0:
            _say('choose %d/%d' % (_n, count))
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


def _residue(text, entries):
    """The stretches the dictionary did not cover, for strings that overflowed.

    Feeding these back into choose() is what fills the dead slots: the first
    greedy pass optimises for the corpus as a whole and leaves a couple of
    hundred entries that nothing ever references."""
    by_first = _plan(entries)
    out = []
    for run in _plain_runs(text):
        n = len(run)
        best = [0] * (n + 1)
        pick = [None] * (n + 1)
        for i in range(n - 1, -1, -1):
            cost, chosen = 1 + best[i + 1], None
            for e, ref, L in by_first.get(run[i], ()):
                if L <= n - i and run.startswith(e, i):
                    c = len(ref) + best[i + L]
                    if c < cost:
                        cost, chosen = c, e
            best[i], pick[i] = cost, chosen
        cur, i = [], 0
        while i < n:
            if pick[i]:
                if cur:
                    out.append(''.join(cur)); cur = []
                i += len(pick[i])
            else:
                cur.append(run[i]); i += 1
        if cur:
            out.append(''.join(cur))
    return out


def over_budget(texts_budgets, entries):
    """[(excess, text)] for everything that will not fit."""
    out = []
    for t, b in texts_budgets:
        n = len(encode(t, entries))
        if n > b:
            out.append((n - b, t))
    return out


def fit(texts_budgets, entries, rounds=6):
    """Refine the entry list until nothing overflows, or it stops improving.

    Each round drops the entries no string actually references and refills the
    slots from the uncovered text of the strings that are still over budget.
    That targets the dictionary at the strings that need it instead of at the
    corpus average."""
    entries = list(entries)
    best, best_excess = list(entries), None
    for _n in range(rounds):
        over = over_budget(texts_budgets, entries)
        excess = sum(x for x, _ in over)
        _say('fit pass %d: %d entries, %d over, %d bytes'
             % (_n + 1, len(entries), len(over), excess))
        if best_excess is None or excess < best_excess:
            best, best_excess = list(entries), excess
        if not over:
            return entries
        used = set()
        for t, _b in texts_budgets:
            by_first = _plan(entries)
            for run in _plain_runs(t):
                i, n = 0, len(run)
                while i < n:
                    for e, _r, L in by_first.get(run[i], ()):
                        if L <= n - i and run.startswith(e, i):
                            used.add(e); i += L; break
                    else:
                        i += 1
        keep = [e for e in entries if e in used]
        room = MAX_ENTRIES - len(keep)
        if room <= 0:
            break
        residue = []
        for _x, t in over:
            residue += _residue(t, entries)
        if not residue:
            break
        extra = [e for e in choose(residue, room) if e not in used]
        if not extra:
            break
        entries = keep + extra
    return best


def reorder(texts_budgets, entries):
    """Kept for callers; bank order now falls out of fit()'s own ranking.

    Ranking by the tightest budget that references an entry made things worse
    once the corpus grew - it promotes entries a handful of short strings need
    and demotes the ones the bulk of the script leans on."""
    return entries
_PLAN = {}


def _plan(entries):
    """Cache the per-entry reference cost, bucketed by first character.

    Rebuilt whenever the entry list changes. Sorting inside encode() for every
    call was most of the build time."""
    key = id(entries), len(entries)
    got = _PLAN.get(key)
    if got is None or got[0] is not entries:
        by_first = {}
        for k, e in enumerate(entries):
            sl = slot(k)
            ref = (bytes([0x0E, sl]) if sl < BANK1 else
                   bytes([0x0E, 0xFF, sl - 256]) if sl < 512 else
                   bytes([0x0E, 0xFE, sl - 512]))
            by_first.setdefault(e[0], []).append((e, ref, len(e)))
        for v in by_first.values():
            v.sort(key=lambda x: -x[2])
        got = (entries, by_first)
        _PLAN.clear()
        _PLAN[key] = got
    return got[1]


def _pack(run, by_first):
    """Cheapest encoding of one plain run.

    Longest match first is not optimal: taking a long entry can strand the
    characters after it, where two shorter ones would have covered the lot. So
    walk backwards and keep the best cost at every position."""
    n = len(run)
    best = [0] * (n + 1)
    pick = [None] * (n + 1)
    for i in range(n - 1, -1, -1):
        cost, chosen = 1 + best[i + 1], None
        for e, ref, L in by_first.get(run[i], ()):
            if L <= n - i and run.startswith(e, i):
                c = len(ref) + best[i + L]
                if c < cost:
                    cost, chosen = c, (ref, L)
        best[i], pick[i] = cost, chosen
    out, i = bytearray(), 0
    while i < n:
        if pick[i] is not None:
            ref, L = pick[i]
            out += ref
            i += L
        else:
            out += wmtool.encode_en(run[i])[:-1]
            i += 1
    return out


def encode(text, entries):
    """Text to bytes, using the cheapest parse the dictionary allows."""
    by_first = _plan(entries)
    out, run, i = bytearray(), [], 0
    while i < len(text):
        c = text[i]
        if c == '<':
            j = text.index('>', i) + 1
            if run:
                out += _pack(''.join(run), by_first); run = []
            out += wmtool.encode_en(text[i:j])[:-1]
            i = j
        elif c == '\n':
            if run:
                out += _pack(''.join(run), by_first); run = []
            out.append(0x0D); i += 1
        else:
            run.append(c); i += 1
    if run:
        out += _pack(''.join(run), by_first)
    out.append(0x00)
    return bytes(out)


def _parse(text, entries):
    """Which entries the optimal parse of `text` actually uses."""
    by_first = _plan(entries)
    out = []
    for run in _plain_runs(text):
        i, n = 0, len(run)
        while i < n:
            for e, _r, L in by_first.get(run[i], ()):
                if L <= n - i and run.startswith(e, i):
                    out.append(e); i += L; break
            else:
                i += 1
    return out


def fit_mixed(fixed, free, free_limit, rounds=14, promote=20):
    """Choose entries for a script split between fixed-length and free strings.

    `fixed` is [(text, budget)] - blocks A and C, written back in place, so every
    one of them has to fit. `free` is the block B texts, which are repacked and
    only have to come in under `free_limit` in total.

    Two things matter more than the raw entry choice. Only the first 254 slots
    encode in two bytes; everything above costs three. And the fixed strings are
    short, so a three-byte reference often costs more than it saves. So the cheap
    bank is seeded from the fixed text alone, then hill-climbed: each round
    promotes the entries that the still-overflowing strings reach for and demotes
    the cheap ones nothing much uses. Any step that pushes the free block over
    its ceiling is measured but not kept."""
    ftexts = [t for t, _b in fixed]
    head = choose(ftexts, BANK1)
    tail = [e for e in choose(ftexts + list(free), MAX_ENTRIES) if e not in set(head)]
    entries = head + tail[:MAX_ENTRIES - len(head)]

    def score(ent):
        over = [len(encode(t, ent)) - b for t, b in fixed]
        return (sum(x for x in over if x > 0),
                sum(1 for x in over if x > 0),
                sum(len(encode(t, ent)) for t in free))

    excess, n, size = score(entries)
    _say('mixed fit: %d bytes over on %d strings, free block %d' % (excess, n, size))
    best = (excess, list(entries), size)
    for _r in range(rounds):
        pos = {e: i for i, e in enumerate(entries)}
        want, cheap_use = {}, {}
        for t, b in fixed:
            used = _parse(t, entries)
            tight = len(encode(t, entries)) > b
            for e in used:
                if pos[e] >= BANK1:
                    if tight:
                        want[e] = want.get(e, 0) + 1
                else:
                    cheap_use[e] = cheap_use.get(e, 0) + 1
        up = [e for e, _c in sorted(want.items(), key=lambda kv: -kv[1])[:promote]]
        if not up:
            break
        cheap = entries[:BANK1]
        down = set(sorted(cheap, key=lambda e: cheap_use.get(e, 0))[:len(up)])
        new_cheap = [e for e in cheap if e not in down] + up
        entries = new_cheap + [e for e in entries if e not in set(new_cheap)]
        excess, n, size = score(entries)
        _say('  round %d: %d bytes over on %d strings, free block %d%s'
             % (_r + 1, excess, n, size, '' if size <= free_limit else '  OVER'))
        if size <= free_limit and excess < best[0]:
            best = (excess, list(entries), size)
        if best[0] == 0:
            return best[1]

    # Whatever is still over is short - an item name, a class, a map nameplate -
    # and too small for the general search to bother with. Give each one its own
    # cheap-bank entry, which is what the old _grow() did, except aimed only at
    # the strings that need it. A name that is its own entry encodes to three
    # bytes flat: the escape, the slot, the terminator.
    entries = list(best[1])
    for _r in range(8):
        over = [(t, b) for t, b in fixed if len(encode(t, entries)) > b]
        if not over:
            break
        pos = {e: i for i, e in enumerate(entries)}
        cheap_use = {}
        for t, _b in fixed:
            for e in _parse(t, entries):
                if pos[e] < BANK1:
                    cheap_use[e] = cheap_use.get(e, 0) + 1
        add = []
        for t, _b in over:
            runs = _plain_runs(t)
            if not runs:
                continue
            cand = max(runs, key=len)[:24]
            if len(cand) >= 3 and cand not in pos and cand not in add:
                add.append(cand)
        if not add:
            break
        cheap = entries[:BANK1]
        down = set(sorted(cheap, key=lambda e: cheap_use.get(e, 0))[:len(add)])
        new_cheap = add + [e for e in cheap if e not in down]
        cand_entries = new_cheap + [e for e in entries if e not in set(new_cheap)]
        cand_entries = cand_entries[:MAX_ENTRIES]
        excess, n, size = score(cand_entries)
        _say('  rescue %d: %d bytes over on %d strings, free block %d%s'
             % (_r + 1, excess, n, size, '' if size <= free_limit else '  OVER'))
        if size > free_limit:
            break
        entries = cand_entries
        if excess < best[0]:
            best = (excess, list(entries), size)
        if excess == 0:
            break
    return best[1]


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


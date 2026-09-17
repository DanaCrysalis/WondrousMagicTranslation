#!/usr/bin/env python3
"""The second LZSS - both directions.

`plates.py` has had the decompressor since the nameplates were found. This adds
the compressor, which is what the battle font needs: the block at $152000 has to
be rewritten with a Latin font, and there was no way to put a block back.

Format, as decoded from $02:D1D9 (see docs/compression.md):

    uint16  uncompressed size
    uint16  0
    then groups of:
      control byte, 8 flags, MSB first; each flag consumes one byte
        flag 0            literal
        flag 1, b < $10   offset = b & $0F, copy 2 bytes from dest - offset - 1
        flag 1, b >= $10  offset = ((b & $0F) << 8) | next   (12 bits)
                          length = (b >> 4) + 2
                          b >= $F0: length = a third byte + 17
                          copy from dest - offset - 1, overlapping

So the encodable shapes are

    length 2         distance 1-16     one byte
    length 3-16      distance 1-4096   two bytes
    length 17-272    distance 1-4096   three bytes

A literal is one byte. Every token also costs one flag bit, so the flag is free
to ignore when choosing between them - what matters is the byte count.

The decompressor stops the moment the destination pointer reaches the end
($82:D1C7 `CPX $04 / BCS`), and it tests that *before* fetching each token, so a
final group with unused flags costs nothing and needs no terminator. It also
means a match must not overrun: the last token has to land exactly on the end,
or the tail of the copy is written past the destination. The matcher below never
proposes a length longer than what is left, so that cannot happen.

    python3 tools/lzss.py            round-trip every known block in the ROM
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths

MAX_DIST = 4096          # 12-bit offset, distance = offset + 1
MAX_LEN = 272            # $F0 form: third byte + 17
NEAR_DIST = 16           # the one-byte form: offset 0-15
CANDIDATES = 192         # match positions kept per three-byte key


def decompress(data, p, limit):
    """Unpack `limit` bytes starting at `data[p]`. Returns (bytes, end offset)."""
    out = bytearray()
    while len(out) < limit:
        ctrl = data[p]; p += 1
        for _ in range(8):
            if len(out) >= limit:
                return bytes(out), p
            b = data[p]; p += 1
            if not (ctrl & 0x80):
                out.append(b)
            elif b < 0x10:
                src = len(out) - (b & 0x0F) - 1
                out.append(out[src]); out.append(out[src + 1])
            else:
                off = ((b & 0x0F) << 8) | data[p]; p += 1
                if b >= 0xF0:
                    n = data[p] + 17; p += 1
                else:
                    n = (b >> 4) + 2
                src = len(out) - off - 1
                for k in range(n):
                    out.append(out[src + k])
            ctrl = (ctrl << 1) & 0xFF
    return bytes(out), p


def block(rom, off):
    """Unpack the block whose four-byte header sits at `off`."""
    size = rom[off] | rom[off + 1] << 8
    data, end = decompress(rom, off + 4, size)
    assert len(data) == size, 'short block at $%06X' % off
    return data, end


# ------------------------------------------------------------- compressor ---

def _cost(n, dist):
    """Bytes a match of this shape costs, or None if it cannot be encoded."""
    if n >= 17:
        return 3 if n <= MAX_LEN and dist <= MAX_DIST else None
    if n >= 3:
        return 2 if dist <= MAX_DIST else None
    if n == 2:
        return 1 if dist <= NEAR_DIST else None
    return None


def _scan(src):
    """Per position: the longest match reachable, its distance, and whether a
    two-byte match exists inside the near window."""
    n = len(src)
    heads = {}
    best = [(0, 0)] * n
    near = [0] * n
    for i in range(n):
        if i + 2 <= n:
            for s in range(i - 1, max(-1, i - NEAR_DIST) - 1, -1):
                if src[s] == src[i] and src[s + 1] == src[i + 1]:
                    near[i] = i - s
                    break
        if i + 3 <= n:
            key = src[i:i + 3]
            cands = heads.get(key)
            if cands:
                lim = min(MAX_LEN, n - i)
                bl, bd = 0, 0
                for s in reversed(cands):
                    d = i - s
                    if d > MAX_DIST:
                        break
                    k = 0
                    while k < lim and src[s + k] == src[i + k]:
                        k += 1
                    if k > bl:
                        bl, bd = k, d
                        if bl == lim:
                            break
                best[i] = (bl, bd)
            heads.setdefault(key, []).append(i)
            if len(heads[key]) > CANDIDATES:
                heads[key] = heads[key][-CANDIDATES:]
    return best, near


def _parse(src):
    """Cheapest token sequence, by shortest path from the end.

    Greedy is close but not close enough: the plate chain has no slack after it,
    so a block has to come back no bigger than it went in, and greedy came out
    2.5% over. Every token costs one flag bit on top of its bytes, so costs are
    counted in eighths of a byte - literal and near-match 9, the two-byte form
    17, the three-byte form 25 - and a token is chosen by what it leaves behind
    rather than by how long it is.

    Within a cost class every length is the same price, so the inner search is a
    min over a slice of the cost table rather than a loop. A match of length m at
    distance d also gives any shorter length at the same distance, so one
    distance per position is all that needs storing.
    """
    n = len(src)
    best, near = _scan(src)
    INF = float('inf')
    cost = [INF] * (n + 1)
    pick = [None] * n
    cost[n] = 0
    for i in range(n - 1, -1, -1):
        c, p = 9 + cost[i + 1], None
        if near[i] and i + 2 <= n and 9 + cost[i + 2] < c:
            c, p = 9 + cost[i + 2], (2, near[i])
        m, d = best[i]
        if m >= 3:
            hi = min(m, 16)
            tail = cost[i + 3:i + hi + 1]
            v = min(tail)
            if 17 + v < c:
                c, p = 17 + v, (3 + tail.index(v), d)
            if m >= 17:
                tail = cost[i + 17:i + m + 1]
                v = min(tail)
                if 25 + v < c:
                    c, p = 25 + v, (17 + tail.index(v), d)
        cost[i], pick[i] = c, p
    toks, i = [], 0
    while i < n:
        p = pick[i]
        if p is None:
            toks.append(('lit', src[i])); i += 1
        else:
            toks.append(('m', p[0], p[1])); i += p[0]
    return toks


def _emit(tok, out):
    kind = tok[0]
    if kind == 'lit':
        out.append(tok[1])
        return 0
    n, dist = tok[1], tok[2]
    off = dist - 1
    if n == 2:
        out.append(off)
    elif n <= 16:
        out.append(((n - 2) << 4) | (off >> 8))
        out.append(off & 0xFF)
    else:
        out.append(0xF0 | (off >> 8))
        out.append(off & 0xFF)
        out.append(n - 17)
    return 1


def compress(src):
    """Pack `src`. The header is included, so the result is a whole block."""
    src = bytes(src)
    out = bytearray(len(src).to_bytes(2, 'little') + b'\x00\x00')
    toks = _parse(src)
    for g in range(0, len(toks), 8):
        ctrl = 0
        body = bytearray()
        for j, tok in enumerate(toks[g:g + 8]):
            ctrl |= _emit(tok, body) << (7 - j)
        out.append(ctrl)
        out += body
    return bytes(out)


# ------------------------------------------------------------------ check ---

KNOWN = [0x0AF000, 0x0B3D68, 0x0B4A1E, 0x152000]


def main():
    rom = paths.rom()
    for off in KNOWN:
        data, end = block(rom, off)
        enc = compress(data)
        assert decompress(enc, 4, len(data))[0] == data, '$%06X does not round-trip' % off
        print('$%06X  unpacked $%04X  was %d bytes, repacked %d (%+d)'
              % (off, len(data), end - off, len(enc), len(enc) - (end - off)))


if __name__ == '__main__':
    main()

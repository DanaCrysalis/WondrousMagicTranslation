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

    python3 tools/lzss.py check      round-trip every known block in the ROM
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths

MAX_DIST = 4096          # 12-bit offset, distance = offset + 1
MAX_LEN = 272            # $F0 form: third byte + 17
NEAR_DIST = 16           # the one-byte form: offset 0-15


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
    n = len(src)
    heads = {}                       # three-byte key -> most recent positions
    toks, i = [], 0
    while i < n:
        best = _find(src, i, heads, n)
        # Lazy: if starting one byte later beats this by more than the literal
        # costs, take the literal. Only worth asking when we have a match at all.
        if best and i + 1 < n:
            nxt = _find(src, i + 1, heads, n, peek=True)
            if nxt and _gain(nxt) > _gain(best):
                best = None
        if best:
            toks.append(('m', best[0], best[1]))
            for k in range(i, i + best[0]):
                _index(src, k, heads, n)
            i += best[0]
        else:
            toks.append(('lit', src[i]))
            _index(src, i, heads, n)
            i += 1

    out = bytearray(n.to_bytes(2, 'little') + b'\x00\x00')
    for g in range(0, len(toks), 8):
        group = toks[g:g + 8]
        ctrl = 0
        body = bytearray()
        for j, tok in enumerate(group):
            ctrl |= _emit(tok, body) << (7 - j)
        out.append(ctrl)
        out += body
    return bytes(out)


def _index(src, i, heads, n):
    if i + 3 <= n:
        heads.setdefault(src[i:i + 3], []).append(i)


def _gain(m):
    """Bytes saved against writing the run out as literals."""
    return m[0] - _cost(m[0], m[1])


def _find(src, i, heads, n, peek=False):
    """Best (length, distance) at `i`, or None."""
    limit = min(MAX_LEN, n - i)
    if limit < 2:
        return None
    best = None
    # length 2 has its own one-byte form, and only within 16 bytes; it is never
    # worth a search, just a scan of the near window.
    lo = max(0, i - NEAR_DIST)
    for s in range(i - 1, lo - 1, -1):
        if src[s] == src[i] and src[s + 1] == src[i + 1]:
            best = (2, i - s)
            break
    if limit < 3:
        return best
    cands = heads.get(src[i:i + 3])
    if cands:
        for s in reversed(cands[-64:]):
            dist = i - s
            if dist > MAX_DIST:
                break
            k = 0
            while k < limit and src[s + k] == src[i + k]:
                k += 1
            if k >= 3 and (best is None or _gain((k, dist)) > _gain(best)):
                best = (k, dist)
    if best and _cost(best[0], best[1]) >= best[0]:
        return None                  # no cheaper than literals
    return best


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

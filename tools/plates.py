#!/usr/bin/env python3
"""Map nameplates: export to PNG, and put edited PNGs back.

The plates are not text. They are 16x16 characters of 4bpp tile art, drawn in
the same typeface as the Japanese font but redrawn with an outline, so there is
no string anywhere to translate - the pixels are baked.

They live in an LZSS stream that the routine at $90:877A unpacks. That is not
the RUX compressor used for the intro; it is a second scheme, which is why none
of the RUX-based searching ever found them:

    control byte, 8 bits, MSB first; each bit consumes one byte
      bit clear         literal
      bit set, b < $10  offset = b & $0F, copy 2 bytes from dest - offset - 1
      bit set, b >= $10 offset = ((b & $0F) << 8) | next   (12 bits)
                        length = (b >> 4) + 2, or a third byte + 17 when b >= $F0

Each block starts with a four-byte header whose first word is the uncompressed
size; $90:8750 reads it to work out where the destination run ends. Blocks are
laid end to end, so the chain can be walked from the first one.

The two plate blocks are the first two of that chain, unpacked to $7E:4000 and
$7E:6800. Verified: decompressing them reproduces a savestate's WRAM byte for
byte.

    python3 tools/plates.py export out/     dump every plate as a PNG
    python3 tools/plates.py list            just name the offsets and sizes
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
import wmtool

CHAIN = 0x0B3D68                 # first block of the chain
PLATE_BLOCKS = 2                 # the first two hold the nameplates
CHARS_PER_PLATE = 8              # 8 characters per slot, blanks included


def decompress(data, p, limit):
    out = bytearray()
    while len(out) < limit and p < len(data) - 3:
        ctrl = data[p]; p += 1
        for _ in range(8):
            if len(out) >= limit or p >= len(data) - 3:
                return bytes(out), p
            b = data[p]; p += 1
            if not (ctrl & 0x80):
                out.append(b)
            else:
                if b < 0x10:
                    src = len(out) - (b & 0x0F) - 1
                    for k in range(2):
                        out.append(out[src + k])
                else:
                    lo = data[p]; p += 1
                    off = ((b & 0x0F) << 8) | lo
                    n = (data[p] + 17) if b >= 0xF0 else ((b >> 4) + 2)
                    if b >= 0xF0:
                        p += 1
                    src = len(out) - off - 1
                    for k in range(n):
                        out.append(out[src + k])
            ctrl = (ctrl << 1) & 0xFF
    return bytes(out), p


def blocks(rom, first=CHAIN, count=16):
    """Walk the chain: [(header offset, uncompressed size, end offset)]."""
    out, p = [], first
    for _ in range(count):
        size = rom[p] | rom[p + 1] << 8
        if size == 0 or size > 0x8000:
            break
        data, end = decompress(rom, p + 4, size)
        if len(data) != size:
            break
        out.append((p, size, end, data))
        p = end
    return out


def char_pixels(buf, index):
    """One 16x16 character as a list of rows of palette indices.

    Same arrangement the Japanese font uses: eight characters to a $400 block,
    top halves first, bottom halves $200 further on.
    """
    base = (index >> 3) * 0x400 + (index & 7) * 64
    rows = [[0] * 16 for _ in range(16)]
    for half, ho in ((0, 0), (1, 0x200)):
        for tile, ox in ((0, 0), (1, 8)):
            o = base + ho + tile * 32
            for y in range(8):
                p0, p1 = buf[o + y*2], buf[o + y*2 + 1]
                p2, p3 = buf[o + 16 + y*2], buf[o + 16 + y*2 + 1]
                for x in range(8):
                    s = 7 - x
                    rows[half*8 + y][ox + x] = (((p0 >> s) & 1) | (((p1 >> s) & 1) << 1)
                                                | (((p2 >> s) & 1) << 2) | (((p3 >> s) & 1) << 3))
    return rows


PALETTE = [
    (0x42, 0x00, 0x00), (0x94, 0x4a, 0x10), (0xff, 0xd6, 0x94), (0xa5, 0x63, 0x21),
    (0xbd, 0x7b, 0x29), (0x31, 0x00, 0x00), (0x21, 0x73, 0xff), (0x00, 0x5a, 0xef),
] + [(0x20 * (i % 8), 0x20 * (i % 8), 0x20 * (i % 8)) for i in range(8)]


def export(rom, outdir):
    from PIL import Image
    os.makedirs(outdir, exist_ok=True)
    flat = []
    for bi, (_off, size, _end, data) in enumerate(blocks(rom)[:PLATE_BLOCKS]):
        for c in range(size // 128):
            flat.append((bi, c, char_pixels(data, c)))
    n = 0
    for p in range(len(flat) // CHARS_PER_PLATE):
        chars = flat[p*CHARS_PER_PLATE:(p+1)*CHARS_PER_PLATE]
        if all(len(set(v for row in ch[2] for v in row)) <= 1 for ch in chars):
            continue
        im = Image.new('P', (16 * CHARS_PER_PLATE, 16))
        pal = []
        for c in PALETTE:
            pal += list(c)
        im.putpalette(pal + [0] * (768 - len(pal)))
        for i, (_b, _c, rows) in enumerate(chars):
            for y in range(16):
                for x in range(16):
                    im.putpixel((i*16 + x, y), rows[y][x])
        im.save(os.path.join(outdir, 'plate_%02d.png' % p))
        n += 1
    return n


def main():
    rom = wmtool.ROM
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'list'
    ch = blocks(rom)
    if cmd == 'list':
        for off, size, end, _d in ch:
            b, a = wmtool.pc2snes(off)
            print('$%06X (%02X:%04X)  unpacked $%04X  compressed %d bytes'
                  % (off, b, a, size, end - off))
    elif cmd == 'export':
        outdir = sys.argv[2] if len(sys.argv) > 2 else 'plates'
        print('exported %d plates to %s' % (export(rom, outdir), outdir))


if __name__ == '__main__':
    main()

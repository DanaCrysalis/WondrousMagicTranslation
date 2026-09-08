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

Which block a plate lives in is decided at $91:8344: index < 10 takes block 0 at
$16:BD68, otherwise block 1 at $16:CA1E with ten subtracted. Both addresses are
immediates in that code rather than table entries, and the plate is read from
offset index*$400 in whichever block was unpacked, so the two blocks are
independent of each other and of the seven that follow them - those are pointed
at from a table at $08874E and do not care what happens here. The only rule is
that block 0 and block 1 together must still fit between $0B3D68 and $0B5644,
where the table-pointed blocks begin.

    python3 tools/plates.py list            name the offsets and sizes
    python3 tools/plates.py export out/     dump every plate as a PNG
    python3 tools/plates.py draw out/       draw English plates from the names
                                            in assets/plates/, to edit by hand

`build/plates_patch.py` compiles whatever is in `assets/plates/` back into the
ROM on every build, so a plate is changed by editing its PNG and rebuilding.
Keep the size at 128x16 and use only the three colours the art uses:

    index 2   letter body        index 8   outline        index 9   field
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
import wmtool

CHAIN = 0x0B3D68                 # first block of the chain
PLATE_BLOCKS = 2                 # the first two hold the nameplates
CHARS_PER_PLATE = 8              # 8 characters per slot, blanks included
PLATE_BYTES = 0x400              # what $91:835E multiplies the index by
PLATES = 20
BODY, OUTLINE, FIELD = 2, 8, 9   # the only three colours the art uses
BUDGET = 0x0B5644 - CHAIN        # blocks 0 and 1 must still fit below this
# $91:8344 picks the block and both addresses are immediates, so this is where
# the two plate blocks are really named. Everything here reads them from the
# code rather than from the chain walk: once block 0 changes length the walk
# lands in the middle of nothing, and the game never walked it anyway.
HEADS = (0x088349, 0x088354)     # the LDX #$xxxx of each; LDA #bank follows


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


def heads(rom):
    """Where the two plate blocks are, read out of $91:8349 and $91:8354."""
    out = []
    for op in HEADS:
        assert rom[op] == 0xA2 and rom[op + 3] == 0xA9, \
            'the plate block selector at $%06X is not what it was' % op
        addr = rom[op + 1] | rom[op + 2] << 8
        out.append((rom[op + 4] & 0x7F) * 0x8000 + (addr & 0x7FFF))
    return out


def plate_blocks(rom):
    """The two plate blocks, unpacked. [(offset, size, end, data)]."""
    out = []
    for off in heads(rom):
        size = rom[off] | rom[off + 1] << 8
        data, end = decompress(rom, off + 4, size)
        assert len(data) == size, 'short plate block at $%06X' % off
        out.append((off, size, end, data))
    return out


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


def write_char(buf, index, rows):
    """Inverse of char_pixels: 16 rows of palette indices back into the block."""
    base = (index >> 3) * PLATE_BYTES + (index & 7) * 64
    for half, ho in ((0, 0), (1, 0x200)):
        for tile, ox in ((0, 0), (1, 8)):
            o = base + ho + tile * 32
            for y in range(8):
                v = [0, 0, 0, 0]
                for x in range(8):
                    p = rows[half * 8 + y][ox + x]
                    for b in range(4):
                        v[b] |= ((p >> b) & 1) << (7 - x)
                buf[o + y*2], buf[o + y*2 + 1] = v[0], v[1]
                buf[o + 16 + y*2], buf[o + 16 + y*2 + 1] = v[2], v[3]


PALETTE = [
    (0x42, 0x00, 0x00), (0x94, 0x4a, 0x10), (0xff, 0xd6, 0x94), (0xa5, 0x63, 0x21),
    (0xbd, 0x7b, 0x29), (0x31, 0x00, 0x00), (0x21, 0x73, 0xff), (0x00, 0x5a, 0xef),
] + [(0x20 * (i % 8), 0x20 * (i % 8), 0x20 * (i % 8)) for i in range(8)]


def export(rom, outdir):
    from PIL import Image
    os.makedirs(outdir, exist_ok=True)
    flat = []
    for bi, (_off, size, _end, data) in enumerate(plate_blocks(rom)):
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


def read_pngs(indir):
    """{plate index: 16 rows of 128 palette indices} from NN_Name.png files."""
    from PIL import Image
    out = {}
    for name in sorted(os.listdir(indir)):
        if not name.endswith('.png') or name.startswith('_'):
            continue
        digits = ''.join(c for c in name.split('_')[0] if c.isdigit())
        if not digits:
            continue
        p = int(digits)
        im = Image.open(os.path.join(indir, name))
        if im.size != (16 * CHARS_PER_PLATE, 16):
            raise SystemExit('%s is %dx%d, must be %dx16'
                             % (name, im.size[0], im.size[1], 16 * CHARS_PER_PLATE))
        if im.mode != 'P':
            raise SystemExit('%s must be a paletted PNG - the pixel values are '
                             'palette indices, not colours' % name)
        px = im.load()
        rows = [[px[x, y] for x in range(16 * CHARS_PER_PLATE)] for y in range(16)]
        bad = {v for row in rows for v in row} - {BODY, OUTLINE, FIELD}
        if bad:
            raise SystemExit('%s uses palette indices %s; only %d (body), %d '
                             '(outline) and %d (field) exist here'
                             % (name, sorted(bad), BODY, OUTLINE, FIELD))
        if p in out:
            raise SystemExit('two files claim plate %d' % p)
        out[p] = rows
    return out


def apply(rom, indir):
    """Compile assets/plates back into blocks 0 and 1. Returns (bytes, budget).

    Both blocks are rewritten even when only one plate changed, because the
    compressed length of block 0 decides where block 1 starts. They are laid end
    to end from $0B3D68 and must not reach $0B5644, where the first of the
    table-pointed blocks begins.
    """
    import lzss
    plate_rows = read_pngs(indir)
    bufs = [bytearray(d) for _, _, _, d in plate_blocks(rom)]
    for p, rows in plate_rows.items():
        if p >= PLATES:
            raise SystemExit('plate %d: there are %d' % (p, PLATES))
        block, slot = divmod(p, 10)          # $91:8344: ten plates per block
        for c in range(CHARS_PER_PLATE):
            char = slot * CHARS_PER_PLATE + c
            write_char(bufs[block], char,
                       [row[c*16:(c+1)*16] for row in rows])
    packed = [lzss.compress(bytes(b)) for b in bufs]
    total = sum(len(p) for p in packed)
    if total > BUDGET:
        raise SystemExit(
            'plate blocks are %d bytes, %d fit before $0B5644 (%d over).\n'
            '  Either the art has to compress smaller, or the blocks have to '
            'move: both addresses are immediates (LDX at $%06X and $%06X, each '
            'with its bank in the LDA that follows), so relocating one is three '
            'bytes.' % (total, BUDGET, total - BUDGET, HEADS[0], HEADS[1]))
    at = CHAIN
    for op, blob in zip(HEADS, packed):
        rom[at:at + len(blob)] = blob
        bank, addr = wmtool.pc2snes(at)
        rom[op + 1], rom[op + 2], rom[op + 4] = addr & 0xFF, addr >> 8, bank & 0x7F
        at += len(blob)
    # blank the tail rather than leave a stub of the old block 1 behind, so the
    # next person to walk the chain by hand sees empty space and not half a block
    rom[at:CHAIN + BUDGET] = b'\xff' * (CHAIN + BUDGET - at)
    # read it back the way the game will, through the selector we just patched
    for (_o, _s, _e, got), want in zip(plate_blocks(rom), bufs):
        assert got == bytes(want), 'a plate block does not survive the round trip'
    return total, BUDGET


# ------------------------------------------------------------------- draw ---

def draw(indir, outdir):
    """Render each plate's name in Latin letters, as somewhere to start.

    The Japanese plates are hand-drawn 16x16 characters with an outline. This
    sets the same three colours from the half-width font, outlined by dilation,
    two letters to a character cell - so 16 letters across a plate. It is a
    first pass to edit, not a substitute for drawing them.
    """
    from PIL import Image
    import glyphs
    os.makedirs(outdir, exist_ok=True)
    W = 16 * CHARS_PER_PLATE
    over = []
    for name in sorted(os.listdir(indir)):
        if not name.endswith('.png') or name.startswith('_'):
            continue
        digits = ''.join(c for c in name.split('_')[0] if c.isdigit())
        if not digits:
            continue
        label = name[len(digits) + 1:-4].replace('_', ' ')
        body = [[0] * W for _ in range(16)]
        if len(label) * 8 > W:
            over.append((name, label, len(label)))
            continue
        x0 = (W - len(label) * 8) // 2
        for i, chx in enumerate(label):
            g = glyphs.half(chx)
            for y in range(16):
                for x in range(8):
                    if g[y][x] == 3:
                        body[y][x0 + i*8 + x] = 1
        rows = [[FIELD] * W for _ in range(16)]
        for y in range(16):
            for x in range(W):
                if body[y][x]:
                    rows[y][x] = BODY
                elif any(body[y+dy][x+dx]
                         for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                         if 0 <= y+dy < 16 and 0 <= x+dx < W):
                    rows[y][x] = OUTLINE
        im = Image.new('P', (W, 16))
        pal = []
        for c in PALETTE:
            pal += list(c)
        im.putpalette(pal + [0] * (768 - len(pal)))
        for y in range(16):
            for x in range(W):
                im.putpixel((x, y), rows[y][x])
        im.save(os.path.join(outdir, name))
    return over


def contact(indir, path, scale=3):
    """All the plates stacked into one image, the way assets/_all_plates.png is.

    Twenty plates at 128x16 is nothing to look at one file at a time.
    """
    from PIL import Image
    names = sorted(f for f in os.listdir(indir)
                   if f.endswith('.png') and not f.startswith('_'))
    W = 16 * CHARS_PER_PLATE * scale
    im = Image.new('RGB', (W, len(names) * 16 * scale), (0, 0, 0))
    for i, name in enumerate(names):
        src = Image.open(os.path.join(indir, name)).convert('RGB')
        im.paste(src.resize((W, 16 * scale), Image.NEAREST), (0, i * 16 * scale))
    im.save(path)
    return len(names)


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
    elif cmd == 'draw':
        outdir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(paths.ROOT, 'out')
        over = draw(os.path.join(paths.ASSETS, 'plates'), outdir)
        contact(outdir, os.path.join(outdir, '_all_plates.png'))
        print('drew English plates to %s' % outdir)
        for name, label, n in over:
            print('  skipped %s: %r is %d letters, %d fit'
                  % (name, label, n, 16 * CHARS_PER_PLATE // 8))
        print('copy into assets/plates/ and edit; the build reads that directory')
    else:
        raise SystemExit('usage: plates.py [list | export DIR | draw DIR]')


if __name__ == '__main__':
    main()

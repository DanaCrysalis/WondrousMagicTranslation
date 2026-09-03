#!/usr/bin/env python3
"""Wondrous Magic (SFC) text tool - engine model verified against ROM code.

Engine facts (all confirmed by disassembly at $90:9543 / $90:9605 / $90:9859):
  entry        $90:9519 -> $90:9543   main loop at $90:957C
  stream read  $90:9859   reads DB:Y, Y++ ; on Y wrap DB++ and Y=$8000 (LoROM safe)
  renderer     $90:9605   writes one 16-bit tilemap word to $7E:2C00 + (row&15)*32 + (col&15)*2
  cursor       $AE = column, $AF = row, $B4 = left margin  (buffer is 16 cols x 16 rows)
  tile word    tile = ((c>>3)*32) + ((c&7)*2) + (flags & $11) ; attr = (flags & $C0) | $AD ^ $20
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths

import json, sys

ROM_PATH = paths.ROM_IN
ROM = open(ROM_PATH, 'rb').read()

# ---- control codes: (name, parameter bytes) -------------------------------
CTRL = {
    0x00: ('END',  0),   # falls out of the CMP chain -> PLB/RTL. THE terminator.
    0x01: ('NOP',  0),   # branches back to loop top, consumes nothing
    0x02: ('NAME', 2),   # $9751 print string via $7E:3208 table (arg0=slot, arg1=?)
    0x03: ('NUM7', 2),   # $978B 7-digit decimal
    0x04: ('NUM8', 2),   # $9787 8-digit decimal
    0x05: ('WAIT', 0),   # $96B5 flush + $98BC
    0x06: ('C06',  1),   # $96E1 JSL $10:94F1
    0x07: ('C07',  4),   # $970A JSL $10:94E7
    0x08: ('C08',  1),   # $97FB JSL through $7E:3208 table
    0x09: ('C09',  2),   # $9738 JSL $10:94EB
    0x0A: ('PAGE', 0),   # $96D2 JSL $10:99A4, clears $B8
    0x0B: ('SFX',  1),   # $96EB JSL $00:FBFE
    0x0C: ('C0C',  1),   # $96F5 JSL $00:FB7C, or $10:D7AD when arg==3
    0x0D: ('NL',   0),   # $96BE newline: $AE=$B4, $AF++
}
# $0E-$1D are unhandled: engine falls through and returns -> treat as END.

EXT_TABLE = 0x081675          # $E0-$FF -> 16-bit (glyph<<8 | flags)
FONT_TEXT  = 0x0A8000         # 192 x 16x16 2bpp glyphs, bytes $20-$DF
FONT_KANJI = 0x0AB000         # 256 x 16x16 2bpp glyphs, $1E xx
# glyph g at FONT + (g>>3)*0x200 + (g&7)*32 : 32 bytes (top half) and +0x100 (bottom half)
# uploader: $90:9A67, reads $15:8000,X and $15:8100,X -> WRAM $7E:2E00/$2F00 -> VRAM DMA

_T = json.load(open(os.path.join(paths.DATA,'table.json')))
TBL = {int(k, 16): v for k, v in _T['text'].items()}      # $20-$DF, from ROM font $0A8000
EXT = {int(k, 16): v for k, v in _T['ext'].items()}       # $E0-$E4 flipped text glyphs
KANJI = {int(k, 16): v for k, v in _T['kanji'].items()}   # $1E xx, from ROM font $0AB000


def snes2pc(bank, addr):
    return ((bank & 0x7F) << 15) + (addr - 0x8000)


def pc2snes(off):
    return (0x80 + (off >> 15), 0x8000 + (off & 0x7FFF))


def ext(b):
    o = EXT_TABLE + (b - 0xE0) * 2
    return ROM[o] | ROM[o + 1] << 8


def decode(off, limit=8192):
    """Lossless token list. Stops after the terminator."""
    toks, p = [], off
    while p < off + limit:
        b = ROM[p]; p += 1
        if b >= 0xE0:
            toks.append(('ext', b)); continue
        if b >= 0x20:
            toks.append(('chr', b)); continue
        if b == 0x1E:
            toks.append(('kanji', ROM[p])); p += 1; continue
        if b == 0x1F:
            toks.append(('sym', ROM[p])); p += 1; continue
        name, n = CTRL.get(b, ('END', 0))
        if name == 'END':
            toks.append(('end', b)); break
        toks.append(('ctrl', name, bytes(ROM[p:p + n]))); p += n
    return toks, p


def text(toks):
    out = []
    for t in toks:
        k = t[0]
        if k == 'chr':
            out.append(TBL.get(t[1], '[%02X]' % t[1]))
        elif k == 'kanji':
            out.append(KANJI.get(t[1], '{%02X}' % t[1]))
        elif k == 'sym':
            out.append('<S%02X>' % t[1])
        elif k == 'ext':
            out.append(EXT.get(t[1], '<E%02X>' % t[1]))
        elif k == 'ctrl':
            out.append('\n' if t[1] == 'NL' else
                       '<%s%s>' % (t[1], ':' + t[2].hex().upper() if t[2] else ''))
        else:
            out.append('' if t[1] == 0 else '<END%02X>' % t[1])
    return ''.join(out)


def encode(s):
    """Inverse of text() for round-tripping. Raises on unknown glyph."""
    rev = {v: k for k, v in TBL.items()}
    revk = {v: k for k, v in KANJI.items()}
    out, i = bytearray(), 0
    while i < len(s):
        c = s[i]
        if c == '\n':
            out.append(0x0D); i += 1; continue
        if c == '{':
            j = s.index('}', i); out += bytes([0x1E, int(s[i+1:j], 16)]); i = j+1; continue
        if c == '<':
            j = s.index('>', i); body = s[i+1:j]; i = j+1
            if body.startswith('G'):
                out.append(int(body[1:], 16))
            elif body.startswith('S'):   out += bytes([0x1F, int(body[1:], 16)]); continue
            if body.startswith('E'):   out.append(int(body[1:], 16)); continue
            if body.startswith('END'): out.append(int(body[3:], 16)); continue
            nm, _, arg = body.partition(':')
            code = next(k for k, v in CTRL.items() if v[0] == nm)
            out.append(code); out += bytes.fromhex(arg) if arg else b''
            continue
        if c == '[':
            j = s.index(']', i); out.append(int(s[i+1:j], 16)); i = j+1; continue
        if c in revk and c not in rev:
            out += bytes([0x1E, revk[c]]); i += 1; continue
        out.append(rev[c]); i += 1
    out.append(0x00)
    return bytes(out)


PTR_TABLES = [
    # (rom offset, entries, bank) - verified: all 283 land exactly on string starts
    (0x090F00, 283, 0x92),
]

TEXT_BLOCKS = [
    ('C', 0x090000, 0x090EF6),   # menus, windows, status/system text (bank $92 $8000)
    ('A', 0x0912C0, 0x0976C5),   # item / spell / equipment text
    ('B', 0x098340, 0x0A5625),   # main story script
]

if __name__ == '__main__':
    for name, a, b in TEXT_BLOCKS:
        p, n = a, 0
        while p < b:
            toks, q = decode(p)
            bank, addr = pc2snes(p)
            print('=== %s#%04d  ROM $%06X  CPU $%02X:%04X  %d bytes' % (name, n, p, bank, addr, q - p))
            print(text(toks))
            p, n = q, n + 1


# ---------------------------------------------------------------- English ----
# Script byte b renders as ASCII b (glyph h = b - $1F draws ASCII h + $1F), so
# English text is literally its own bytes. Two spaces exist:
#   ' '      $7F  half-width, for prose
#   '\u3000' $20  full-width, one whole cell - keep window frames aligned with it
def encode_en(s):
    out, i = bytearray(), 0
    while i < len(s):
        c = s[i]
        if c == '\n':
            out.append(0x0D); i += 1
        elif c == '\u3000':
            out.append(0x20); i += 1
        elif c == ' ':
            out.append(0x7F); i += 1
        elif c == '<':
            j = s.index('>', i); body = s[i+1:j]; i = j + 1
            if body.startswith('G'):
                out.append(int(body[1:], 16))
            elif body.startswith('S'):
                out += bytes([0x1F, int(body[1:], 16)])
            elif body.startswith('E'):
                out.append(int(body[1:], 16))
            elif body.startswith('END'):
                out.append(int(body[3:], 16))
            else:
                nm, _, arg = body.partition(':')
                out.append(next(k for k, v in CTRL.items() if v[0] == nm))
                out += bytes.fromhex(arg) if arg else b''
        else:
            b = ord(c)
            assert 0x21 <= b <= 0x7E, 'not encodable: %r in %r' % (c, s)
            out.append(b); i += 1
        continue
    out.append(0x00)
    return bytes(out)


def cells(s):
    """Cell width of an English line: half-width glyphs are half a cell."""
    n = 0.0
    i = 0
    while i < len(s):
        c = s[i]
        if c == '<':
            j = s.index('>', i) + 1
            n += 0.5 if s[i+1] == 'G' else 0.0        # a manufactured glyph is half a cell
            i = j; continue
        if c == '\n':
            i += 1; continue
        n += 1.0 if c == '\u3000' else 0.5
        i += 1
    return n

#!/usr/bin/env python3
"""RUX - the LZSS variant used by Wondrous Magic.

Decompressor lives at $A6:8B3E. Format:

    "RUX "                       magic
    uint16 decompressed size
    uint16 0
    then groups of: uint16 control word, MSB first, 16 flags
        flag 0 -> one literal byte
        flag 1 -> uint16 w
                  w & $F000 != 0 : length = w >> 12, offset = w & $0FFF
                  w & $F000 == 0 : offset = w & $0FFF, then a byte, length = byte + $10
                  copy length + 1 bytes from (dest - offset - 1), overlapping
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths


def decompress(data, off):
    assert data[off:off+4] == b'RUX ', 'not a RUX block'
    size = data[off+4] | data[off+5] << 8
    assert (data[off+6] | data[off+7] << 8) == 0
    p = off + 8
    out = bytearray()
    while len(out) < size:
        ctrl = data[p] | data[p+1] << 8
        p += 2
        for _ in range(16):
            if len(out) >= size:
                break
            bit = (ctrl >> 15) & 1
            ctrl = (ctrl << 1) & 0xFFFF
            if not bit:
                out.append(data[p]); p += 1
                continue
            w = data[p] | data[p+1] << 8
            p += 2
            if w & 0xF000:
                length = (w >> 12) & 0x0F
            else:
                length = data[p] + 0x10
                p += 1
            src = len(out) - (w & 0x0FFF) - 1
            for k in range(length + 1):
                out.append(out[src + k])
    return bytes(out[:size]), p - off


if __name__ == '__main__':
    rom = open(paths.ROM_IN,'rb').read()
    data, used = decompress(rom, 0x132000)
    print('ROM $132000 ($A6:A000): %d compressed bytes -> %d bytes' % (used, len(data)))
    open(os.path.join(paths.DATA,'rux_archive.bin'),'wb').write(data)


def compress(data):
    """Greedy LZSS in the same format. Output is accepted by $A6:8B3E."""
    out = bytearray(b'RUX ' + len(data).to_bytes(2, 'little') + b'\x00\x00')
    pos, group, flags, nbits = 0, bytearray(), 0, 0
    index = {}
    while pos < len(data):
        best_len, best_off = 0, 0
        key = data[pos:pos+3]
        if len(key) == 3:
            for cand in reversed(index.get(bytes(key), ())):
                off = pos - cand - 1
                if off > 0x0FFF:
                    break
                n = 0
                while n < 0x110 and pos + n < len(data) and data[cand + n] == data[pos + n]:
                    n += 1
                if n > best_len:
                    best_len, best_off = n, off
                    if n >= 0x110:
                        break
        if best_len >= 3:
            length = best_len - 1                     # encoder stores length, copies length+1
            if length <= 0x0F:
                w = (length << 12) | best_off
                group += w.to_bytes(2, 'little')
            else:
                group += (best_off & 0x0FFF).to_bytes(2, 'little')
                group.append(length - 0x10)
            flags |= 1 << (15 - nbits)
            n = best_len
        else:
            group.append(data[pos]); n = 1
        for k in range(n):
            if pos + k + 3 <= len(data):
                index.setdefault(bytes(data[pos+k:pos+k+3]), []).append(pos + k)
        pos += n
        nbits += 1
        if nbits == 16:
            out += flags.to_bytes(2, 'little') + group
            group, flags, nbits = bytearray(), 0, 0
    if nbits:
        out += flags.to_bytes(2, 'little') + group
    return bytes(out)

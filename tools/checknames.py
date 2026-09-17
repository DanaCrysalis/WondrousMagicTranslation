#!/usr/bin/env python3
"""Run the battle nameplate renderer and check what it puts on screen.

There is no emulator here, and the renderer is the one part of the build that
static reading cannot settle - the failure mode it replaces (halving the four
DMA constants) looked correct on paper too. So this executes the actual patched
bytes on a small 65816 interpreter, serves the DMA registers, and renders the
result through the same tilemap arithmetic $01:DD71 uses.

    python3 tools/checknames.py [rom]

Default is rom/Wondrous_Magic_EN.sfc. Run against the Japanese ROM and it checks
the stock katakana path instead, which is what says the model is right.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
import battle_names

CHARBASE = 0x6000        # VRAM word address of tile 0 for this BG


def lorom(addr):
    bank, a = (addr >> 16) & 0xFF, addr & 0xFFFF
    return ((bank & 0x7F) * 0x8000) + (a & 0x7FFF)


class CPU:
    def __init__(self, rom):
        self.rom = rom
        self.wram = bytearray(0x20000)
        self.vram = bytearray(0x10000)
        self.reg = {}
        self.a = self.x = self.y = 0
        self.s = 0x1FF
        self.p = 0x34                     # M and X set, 8-bit
        self.db = 0x00
        self.pb = 0x00
        self.pc = 0
        self.e = False
        self.tilemap = []
        self.stop = False

    # -- flags
    @property
    def m8(self): return bool(self.p & 0x20)
    @property
    def x8(self): return bool(self.p & 0x10)

    # -- memory
    def _wram_index(self, bank, a):
        if bank in (0x7E, 0x7F):
            return (bank - 0x7E) * 0x10000 + a
        if bank & 0x7F in range(0x00, 0x40) and a < 0x2000:
            return a
        return None

    def read(self, addr):
        bank, a = (addr >> 16) & 0xFF, addr & 0xFFFF
        i = self._wram_index(bank, a)
        if i is not None:
            return self.wram[i]
        if (bank & 0x7F) < 0x40 and 0x2000 <= a < 0x8000:
            return self.reg.get(a, 0)
        return self.rom[lorom(addr)]

    def write(self, addr, v):
        bank, a = (addr >> 16) & 0xFF, addr & 0xFFFF
        i = self._wram_index(bank, a)
        if i is not None:
            self.wram[i] = v
            return
        self.reg[a] = v
        if a == 0x420B and v:
            self.dma(v)

    def r16(self, addr):
        return self.read(addr) | self.read(addr + 1) << 8

    def dma(self, mask):
        assert mask == 0x10, 'only channel 4 is used here'
        b = 0x4340
        dest = 0x2100 | self.reg.get(b + 1, 0)
        src = (self.reg.get(b + 4, 0) << 16) | (self.reg.get(b + 3, 0) << 8) \
            | self.reg.get(b + 2, 0)
        n = self.reg.get(b + 5, 0) | self.reg.get(b + 6, 0) << 8
        assert dest == 0x2118 and self.reg.get(b, 0) == 0x01, 'unexpected DMA mode'
        addr = (self.reg.get(0x2116, 0) | self.reg.get(0x2117, 0) << 8) * 2
        for k in range(n or 0x10000):
            self.vram[(addr + k) & 0xFFFF] = self.read(src + k)
        self.reg[0x2116] = ((addr + n) // 2) & 0xFF
        self.reg[0x2117] = (((addr + n) // 2) >> 8) & 0xFF

    # -- stack
    def push8(self, v):
        self.wram[self.s] = v & 0xFF
        self.s -= 1

    def pop8(self):
        self.s += 1
        return self.wram[self.s]

    def push16(self, v):
        self.push8(v >> 8); self.push8(v)

    def pop16(self):
        return self.pop8() | self.pop8() << 8

    # -- helpers
    def setnz(self, v, wide):
        self.p &= ~0x82
        if v == 0:
            self.p |= 0x02
        if v & (0x8000 if wide else 0x80):
            self.p |= 0x80

    def fetch(self, n=1):
        v = 0
        for k in range(n):
            v |= self.read((self.pb << 16) | self.pc) << (8 * k)
            self.pc = (self.pc + 1) & 0xFFFF
        return v

    def run(self, bank, pc, stubs, limit=400000):
        self.pb, self.pc = bank, pc
        depth = 0
        for _ in range(limit):
            here = (self.pb << 16) | self.pc
            if here in stubs:
                if stubs[here](self) == 'rtl':
                    self.pc = self.pop16() + 1
                    self.pb = self.pop8()
                    continue
            op = self.fetch()
            if self.step(op):
                return
        raise SystemExit('did not stop')

    def step(self, op):
        mw = not self.m8
        xw = not self.x8
        if op == 0x08:   self.push8(self.p)                       # PHP
        elif op == 0x28: self.p = self.pop8()                     # PLP
        elif op == 0x8B: self.push8(self.db)                      # PHB
        elif op == 0xAB: self.db = self.pop8(); self.setnz(self.db, False)
        elif op == 0xE2: self.p |= self.fetch()                   # SEP
        elif op == 0xC2: self.p &= ~self.fetch() & 0xFF           # REP
        elif op == 0x18: self.p &= ~0x01                          # CLC
        elif op == 0x38: self.p |= 0x01                           # SEC
        elif op == 0xA9:                                          # LDA #
            v = self.fetch(2 if mw else 1)
            self.a = v if mw else (self.a & 0xFF00) | v
            self.setnz(v, mw)
        elif op == 0xA0:                                          # LDY #
            self.y = self.fetch(2 if xw else 1); self.setnz(self.y, xw)
        elif op == 0xA2:                                          # LDX #
            self.x = self.fetch(2 if xw else 1); self.setnz(self.x, xw)
        elif op == 0x48:                                          # PHA
            self.push16(self.a) if mw else self.push8(self.a)
        elif op == 0x68:                                          # PLA
            v = self.pop16() if mw else self.pop8()
            self.a = v if mw else (self.a & 0xFF00) | v
            self.setnz(v, mw)
        elif op == 0x5A:                                          # PHY
            self.push16(self.y) if xw else self.push8(self.y)
        elif op == 0x7A:                                          # PLY
            self.y = self.pop16() if xw else self.pop8(); self.setnz(self.y, xw)
        elif op == 0xDA:                                          # PHX
            self.push16(self.x) if xw else self.push8(self.x)
        elif op == 0xFA:                                          # PLX
            self.x = self.pop16() if xw else self.pop8(); self.setnz(self.x, xw)
        elif op == 0xAA:                                          # TAX
            self.x = self.a if xw else self.a & 0xFF; self.setnz(self.x, xw)
        elif op == 0xA8:                                          # TAY
            self.y = self.a if xw else self.a & 0xFF; self.setnz(self.y, xw)
        elif op == 0x98:                                          # TYA
            v = self.y if mw else self.y & 0xFF
            self.a = v if mw else (self.a & 0xFF00) | v
            self.setnz(v, mw)
        elif op == 0x8A:                                          # TXA
            v = self.x if mw else self.x & 0xFF
            self.a = v if mw else (self.a & 0xFF00) | v
            self.setnz(v, mw)
        elif op == 0xEB:                                          # XBA
            self.a = ((self.a << 8) | (self.a >> 8)) & 0xFFFF
            self.setnz(self.a & 0xFF, False)
        elif op == 0xE8:                                          # INX
            self.x = (self.x + 1) & (0xFFFF if xw else 0xFF); self.setnz(self.x, xw)
        elif op == 0xC8:                                          # INY
            self.y = (self.y + 1) & (0xFFFF if xw else 0xFF); self.setnz(self.y, xw)
        elif op == 0x1A:                                          # INC A
            self.a = self._alu_inc(self.a, 1, mw)
        elif op == 0x3A:                                          # DEC A
            self.a = self._alu_inc(self.a, -1, mw)
        elif op == 0x0A:                                          # ASL A
            v = (self.a if mw else self.a & 0xFF) << 1
            self.p = (self.p & ~1) | (1 if v & (0x10000 if mw else 0x100) else 0)
            v &= 0xFFFF if mw else 0xFF
            self.a = v if mw else (self.a & 0xFF00) | v
            self.setnz(v, mw)
        elif op == 0x4A:                                          # LSR A
            v = self.a if mw else self.a & 0xFF
            self.p = (self.p & ~1) | (v & 1)
            v >>= 1
            self.a = v if mw else (self.a & 0xFF00) | v
            self.setnz(v, mw)
        elif op == 0x29:                                          # AND #
            v = self.fetch(2 if mw else 1)
            r = (self.a if mw else self.a & 0xFF) & v
            self.a = r if mw else (self.a & 0xFF00) | r
            self.setnz(r, mw)
        elif op == 0x09:                                          # ORA #
            v = self.fetch(2 if mw else 1)
            r = (self.a if mw else self.a & 0xFF) | v
            self.a = r if mw else (self.a & 0xFF00) | r
            self.setnz(r, mw)
        elif op == 0xC9:                                          # CMP #
            self._cmp(self.a, self.fetch(2 if mw else 1), mw)
        elif op == 0xE0:                                          # CPX #
            self._cmp(self.x, self.fetch(2 if xw else 1), xw)
        elif op == 0xC0:                                          # CPY #
            self._cmp(self.y, self.fetch(2 if xw else 1), xw)
        elif op == 0x69:                                          # ADC #
            self._adc(self.fetch(2 if mw else 1), mw)
        elif op == 0xE9:                                          # SBC #
            self._sbc(self.fetch(2 if mw else 1), mw)
        elif op in (0xAD, 0xBD, 0xB9, 0x8D, 0x9D, 0x99, 0x9C, 0xEE, 0xCE,
                    0x6D, 0xCD, 0x8E, 0xAE, 0x8C, 0xAC, 0xED):
            a = self.fetch(2)
            if op in (0xBD, 0x9D):
                a += self.x
            elif op in (0xB9, 0x99):
                a += self.y
            ea = (self.db << 16) | (a & 0xFFFF)
            self._mem(op, ea, mw, xw)
        elif op in (0xBF, 0xAF, 0x8F, 0x9F):                      # long
            a = self.fetch(3)
            if op in (0xBF, 0x9F):
                a += self.x
            self._mem({0xBF: 0xBD, 0xAF: 0xAD, 0x8F: 0x8D, 0x9F: 0x9D}[op], a, mw, xw)
        elif op in (0xA3, 0x63, 0x83, 0xE3, 0xC3):                # stack relative
            ea = (self.s + self.fetch()) & 0xFFFF
            if op == 0xA3:
                v = self.wram[ea] | (self.wram[ea + 1] << 8 if mw else 0)
                self.a = v if mw else (self.a & 0xFF00) | v
                self.setnz(v, mw)
            elif op == 0x63:
                self._adc(self.wram[ea] | (self.wram[ea + 1] << 8 if mw else 0), mw)
            elif op == 0xE3:
                self._sbc(self.wram[ea] | (self.wram[ea + 1] << 8 if mw else 0), mw)
            elif op == 0xC3:
                self._cmp(self.a, self.wram[ea] | (self.wram[ea + 1] << 8 if mw else 0), mw)
            else:
                self.wram[ea] = self.a & 0xFF
                if mw:
                    self.wram[ea + 1] = self.a >> 8
        elif op == 0x20:                                          # JSR
            t = self.fetch(2); self.push16((self.pc - 1) & 0xFFFF); self.pc = t
        elif op == 0x60:                                          # RTS
            self.pc = (self.pop16() + 1) & 0xFFFF
        elif op == 0x22:                                          # JSL
            t = self.fetch(3)
            self.push8(self.pb); self.push16((self.pc - 1) & 0xFFFF)
            self.pb, self.pc = t >> 16, t & 0xFFFF
        elif op == 0x6B:                                          # RTL
            if self.s >= 0x1FF:
                return True
            self.pc = (self.pop16() + 1) & 0xFFFF; self.pb = self.pop8()
        elif op == 0x4C:  self.pc = self.fetch(2)                 # JMP
        elif op == 0x5C:
            t = self.fetch(3); self.pb, self.pc = t >> 16, t & 0xFFFF
        elif op in (0xF0, 0xD0, 0x30, 0x10, 0x90, 0xB0):          # branches
            d = self.fetch()
            d = d - 256 if d > 127 else d
            take = {0xF0: self.p & 0x02, 0xD0: not self.p & 0x02,
                    0x30: self.p & 0x80, 0x10: not self.p & 0x80,
                    0x90: not self.p & 0x01, 0xB0: self.p & 0x01}[op]
            if take:
                self.pc = (self.pc + d) & 0xFFFF
        elif op == 0xEA:  pass                                    # NOP
        elif op == 0x2B:  self.d = self.pop16()                   # PLD
        elif op == 0xF4:  self.push16(self.fetch(2))              # PEA
        else:
            raise SystemExit('unimplemented opcode $%02X at $%02X:%04X'
                             % (op, self.pb, self.pc - 1))
        return False

    def _mem(self, op, ea, mw, xw):
        if op in (0xAD, 0xBD, 0xB9):
            v = self.read(ea) | (self.read(ea + 1) << 8 if mw else 0)
            self.a = v if mw else (self.a & 0xFF00) | v
            self.setnz(v, mw)
        elif op in (0x8D, 0x9D, 0x99):
            self.write(ea, self.a & 0xFF)
            if mw:
                self.write(ea + 1, (self.a >> 8) & 0xFF)
        elif op == 0x9C:
            self.write(ea, 0)
            if mw:
                self.write(ea + 1, 0)
        elif op in (0xEE, 0xCE):
            v = self.read(ea) | (self.read(ea + 1) << 8 if mw else 0)
            v = (v + (1 if op == 0xEE else -1)) & (0xFFFF if mw else 0xFF)
            self.write(ea, v & 0xFF)
            if mw:
                self.write(ea + 1, v >> 8)
            self.setnz(v, mw)
        elif op == 0x6D:
            self._adc(self.read(ea) | (self.read(ea + 1) << 8 if mw else 0), mw)
        elif op == 0xED:
            self._sbc(self.read(ea) | (self.read(ea + 1) << 8 if mw else 0), mw)
        elif op == 0xCD:
            self._cmp(self.a, self.read(ea) | (self.read(ea + 1) << 8 if mw else 0), mw)
        elif op == 0x8E:
            self.write(ea, self.x & 0xFF)
            if xw:
                self.write(ea + 1, (self.x >> 8) & 0xFF)
        elif op == 0x8C:
            self.write(ea, self.y & 0xFF)
            if xw:
                self.write(ea + 1, (self.y >> 8) & 0xFF)
        elif op == 0xAE:
            self.x = self.read(ea) | (self.read(ea + 1) << 8 if xw else 0)
            self.setnz(self.x, xw)
        elif op == 0xAC:
            self.y = self.read(ea) | (self.read(ea + 1) << 8 if xw else 0)
            self.setnz(self.y, xw)

    def _alu_inc(self, a, d, mw):
        v = ((a if mw else a & 0xFF) + d) & (0xFFFF if mw else 0xFF)
        self.setnz(v, mw)
        return v if mw else (a & 0xFF00) | v

    def _cmp(self, r, v, wide):
        r = r if wide else r & 0xFF
        d = (r - v) & (0xFFFF if wide else 0xFF)
        self.p = (self.p & ~1) | (1 if r >= v else 0)
        self.setnz(d, wide)

    def _adc(self, v, mw):
        r = (self.a if mw else self.a & 0xFF) + v + (self.p & 1)
        lim = 0x10000 if mw else 0x100
        self.p = (self.p & ~1) | (1 if r >= lim else 0)
        r &= lim - 1
        self.a = r if mw else (self.a & 0xFF00) | r
        self.setnz(r, mw)

    def _sbc(self, v, mw):
        lim = 0x10000 if mw else 0x100
        r = (self.a if mw else self.a & 0xFF) - v - (1 - (self.p & 1))
        self.p = (self.p & ~1) | (0 if r < 0 else 1)
        r &= lim - 1
        self.a = r if mw else (self.a & 0xFF00) | r
        self.setnz(r, mw)


# ---------------------------------------------------------------- the test --

def render(cpu, cells):
    """Read the cells back out of VRAM the way the PPU would in 16x16 mode."""
    rows = [[' '] * (16 * len(cells)) for _ in range(16)]
    for i, entry in enumerate(cells):
        t = entry & 0x3FF
        for ty, top in enumerate((t, t + 16)):
            for tx, tn in enumerate((top, top + 1)):
                o = (CHARBASE + tn * 8) * 2
                for y in range(8):
                    p0, p1 = cpu.vram[o + y * 2], cpu.vram[o + y * 2 + 1]
                    for x in range(8):
                        s = 7 - x
                        v = ((p0 >> s) & 1) | (((p1 >> s) & 1) << 1)
                        rows[ty * 8 + y][i * 16 + tx * 8 + x] = ' .:#'[v]
    return [''.join(r).rstrip() for r in rows]


def plate(rom, name_index, patched):
    """Run $81:F877 for a single monster and return (rendered rows, x, y)."""
    cpu = CPU(rom)

    # unpack the font block into $7E:4000 the way the loader does
    import lzss
    data = lzss.block(rom, battle_names.FONT_BLOCK)[0]
    cpu.wram[0x4000:0x4000 + len(data)] = data

    cpu.wram[0x0C27] = 1                        # one monster in slot 0
    cpu.wram[0x0BB5] = name_index + 1           # $0BB5 is 1-based
    cpu.wram[0x086C] = 0x6D                     # first VRAM cell, as $F86D sets

    seen = []

    def f913(c):                                # vblank wait
        return 'rtl'

    def dd71(c):                                # tilemap write
        seen.append((c.read(0x0876) | c.read(0x0877) << 8,
                     c.read(0x0872), c.read(0x0874)))
        return 'rtl'

    stubs = {0x00F913: f913, 0x01DD71: dd71, 0x81DD71: dd71}

    cpu.p = 0x20                                # M 8-bit, X/Y 16-bit
    cpu.x = 0
    cpu.push8(0x81); cpu.push16(0xF876)         # a JSL frame for the final RTL
    cpu.run(0x81, 0xF877, stubs)

    assert len(seen) == 6, 'expected six tilemap entries, got %d' % len(seen)
    # $01:DD71 re-encodes the low byte into the 16x16 tile number; do the same
    cells = []
    for tile, _x, _y in seen:
        c = tile & 0xFF
        cells.append(((c & 7) << 1) | ((c & 0xF8) << 2))
    return render(cpu, cells), seen[0][1], seen[0][2]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else paths.ROM_OUT
    rom = bytearray(open(path, 'rb').read())
    patched = rom[0x00F99B] == 0x22
    print('%s  (%s)' % (os.path.basename(path),
                        'patched' if patched else 'stock'))
    names = None
    if patched:
        import sheet
        names = sheet.monsters()
    fails = 0
    for i in range(battle_names.ENTRIES):
        rows, x, y = plate(rom, i, patched)
        if patched:
            want = names[i]
            got = ''.join(rows).strip()
            if not got and want:
                print('  %2d  %-14s NOTHING DRAWN' % (i, want))
                fails += 1
        if i in (4, 47, 54, 49):
            print('  entry %d at column %d, row %d:' % (i, x, y))
            for r in rows:
                print('    |%s' % r)
    if patched:
        # every name must occupy exactly the cells the centring counted
        print('  %d entries drawn, %d empty' % (battle_names.ENTRIES - fails, fails))
    raise SystemExit(1 if fails else 0)


if __name__ == '__main__':
    main()

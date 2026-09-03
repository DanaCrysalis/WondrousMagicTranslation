#!/usr/bin/env python3
# Minimal 65816 disassembler, LoROM-aware.
import sys

# opcode -> (mnemonic, mode)
# modes: imp, imm_m, imm_x, imm8, dp, dpx, dpy, idp, idpx, idpy, idpl, idply,
# abs, absx, absy, absl, abslx, ind, indx, indl, rel, rell, sr, sry, bm, acc
OPS = {}
def d(o,m,a): OPS[o]=(m,a)
tbl = """
00 BRK imm8
01 ORA idpx
02 COP imm8
03 ORA sr
04 TSB dp
05 ORA dp
06 ASL dp
07 ORA idpl
08 PHP imp
09 ORA imm_m
0A ASL acc
0B PHD imp
0C TSB abs
0D ORA abs
0E ASL abs
0F ORA absl
10 BPL rel
11 ORA idpy
12 ORA idp
13 ORA sry
14 TRB dp
15 ORA dpx
16 ASL dpx
17 ORA idply
18 CLC imp
19 ORA absy
1A INC acc
1B TCS imp
1C TRB abs
1D ORA absx
1E ASL absx
1F ORA abslx
20 JSR abs
21 AND idpx
22 JSL absl
23 AND sr
24 BIT dp
25 AND dp
26 ROL dp
27 AND idpl
28 PLP imp
29 AND imm_m
2A ROL acc
2B PLD imp
2C BIT abs
2D AND abs
2E ROL abs
2F AND absl
30 BMI rel
31 AND idpy
32 AND idp
33 AND sry
34 BIT dpx
35 AND dpx
36 ROL dpx
37 AND idply
38 SEC imp
39 AND absy
3A DEC acc
3B TSC imp
3C BIT absx
3D AND absx
3E ROL absx
3F AND abslx
40 RTI imp
41 EOR idpx
42 WDM imm8
43 EOR sr
44 MVP bm
45 EOR dp
46 LSR dp
47 EOR idpl
48 PHA imp
49 EOR imm_m
4A LSR acc
4B PHK imp
4C JMP abs
4D EOR abs
4E LSR abs
4F EOR absl
50 BVC rel
51 EOR idpy
52 EOR idp
53 EOR sry
54 MVN bm
55 EOR dpx
56 LSR dpx
57 EOR idply
58 CLI imp
59 EOR absy
5A PHY imp
5B TCD imp
5C JML absl
5D EOR absx
5E LSR absx
5F EOR abslx
60 RTS imp
61 ADC idpx
62 PER rell
63 ADC sr
64 STZ dp
65 ADC dp
66 ROR dp
67 ADC idpl
68 PLA imp
69 ADC imm_m
6A ROR acc
6B RTL imp
6C JMP ind
6D ADC abs
6E ROR abs
6F ADC absl
70 BVS rel
71 ADC idpy
72 ADC idp
73 ADC sry
74 STZ dpx
75 ADC dpx
76 ROR dpx
77 ADC idply
78 SEI imp
79 ADC absy
7A PLY imp
7B TDC imp
7C JMP indx
7D ADC absx
7E ROR absx
7F ADC abslx
80 BRA rel
81 STA idpx
82 BRL rell
83 STA sr
84 STY dp
85 STA dp
86 STX dp
87 STA idpl
88 DEY imp
89 BIT imm_m
8A TXA imp
8B PHB imp
8C STY abs
8D STA abs
8E STX abs
8F STA absl
90 BCC rel
91 STA idpy
92 STA idp
93 STA sry
94 STY dpx
95 STA dpx
96 STX dpy
97 STA idply
98 TYA imp
99 STA absy
9A TXS imp
9B TXY imp
9C STZ abs
9D STA absx
9E STZ absx
9F STA abslx
A0 LDY imm_x
A1 LDA idpx
A2 LDX imm_x
A3 LDA sr
A4 LDY dp
A5 LDA dp
A6 LDX dp
A7 LDA idpl
A8 TAY imp
A9 LDA imm_m
AA TAX imp
AB PLB imp
AC LDY abs
AD LDA abs
AE LDX abs
AF LDA absl
B0 BCS rel
B1 LDA idpy
B2 LDA idp
B3 LDA sry
B4 LDY dpx
B5 LDA dpx
B6 LDX dpy
B7 LDA idply
B8 CLV imp
B9 LDA absy
BA TSX imp
BB TYX imp
BC LDY absx
BD LDA absx
BE LDX absy
BF LDA abslx
C0 CPY imm_x
C1 CMP idpx
C2 REP imm8
C3 CMP sr
C4 CPY dp
C5 CMP dp
C6 DEC dp
C7 CMP idpl
C8 INY imp
C9 CMP imm_m
CA DEX imp
CB WAI imp
CC CPY abs
CD CMP abs
CE DEC abs
CF CMP absl
D0 BNE rel
D1 CMP idpy
D2 CMP idp
D3 CMP sry
D4 PEI dp
D5 CMP dpx
D6 DEC dpx
D7 CMP idply
D8 CLD imp
D9 CMP absy
DA PHX imp
DB STP imp
DC JML indl
DD CMP absx
DE DEC absx
DF CMP abslx
E0 CPX imm_x
E1 SBC idpx
E2 SEP imm8
E3 SBC sr
E4 CPX dp
E5 SBC dp
E6 INC dp
E7 SBC idpl
E8 INX imp
E9 SBC imm_m
EA NOP imp
EB XBA imp
EC CPX abs
ED SBC abs
EE INC abs
EF SBC absl
F0 BEQ rel
F1 SBC idpy
F2 SBC idp
F3 SBC sry
F4 PEA abs
F5 SBC dpx
F6 SBC dpx
F7 SBC idply
F8 SED imp
F9 SBC absy
FA PLX imp
FB XCE imp
FC JSR indx
FD SBC absx
FE INC absx
FF SBC abslx
"""
for line in tbl.strip().split("\n"):
    o,m,a = line.split()
    d(int(o,16), m, a)

SIZE = {'imp':1,'acc':1,'imm8':2,'dp':2,'dpx':2,'dpy':2,'idp':2,'idpx':2,'idpy':2,
        'idpl':2,'idply':2,'sr':2,'sry':2,'rel':2,'abs':3,'absx':3,'absy':3,
        'ind':3,'indx':3,'indl':3,'rell':3,'bm':3,'absl':4,'abslx':4}

def file_to_cpu(off):
    return (0x80 + (off >> 15), 0x8000 + (off & 0x7FFF))

def disasm(data, start, end, m=1, x=1, bank=None):
    """m,x: 1 = 8-bit."""
    pc = start
    out = []
    while pc < end:
        op = data[pc]
        mn, mode = OPS[op]
        if mode == 'imm_m': sz = 2 if m else 3
        elif mode == 'imm_x': sz = 2 if x else 3
        else: sz = SIZE[mode]
        ops = data[pc+1:pc+sz]
        b, ca = file_to_cpu(pc)
        if bank is not None: b = bank
        def w(): return ops[0] | (ops[1] << 8)
        if mode == 'imp' or mode == 'acc': txt = mn
        elif mode in ('imm_m','imm_x'):
            txt = "%s #$%s" % (mn, ("%04X" % w()) if sz == 3 else ("%02X" % ops[0]))
        elif mode == 'imm8': txt = "%s #$%02X" % (mn, ops[0])
        elif mode == 'dp': txt = "%s $%02X" % (mn, ops[0])
        elif mode == 'dpx': txt = "%s $%02X,X" % (mn, ops[0])
        elif mode == 'dpy': txt = "%s $%02X,Y" % (mn, ops[0])
        elif mode == 'idp': txt = "%s ($%02X)" % (mn, ops[0])
        elif mode == 'idpx': txt = "%s ($%02X,X)" % (mn, ops[0])
        elif mode == 'idpy': txt = "%s ($%02X),Y" % (mn, ops[0])
        elif mode == 'idpl': txt = "%s [$%02X]" % (mn, ops[0])
        elif mode == 'idply': txt = "%s [$%02X],Y" % (mn, ops[0])
        elif mode == 'sr': txt = "%s $%02X,S" % (mn, ops[0])
        elif mode == 'sry': txt = "%s ($%02X,S),Y" % (mn, ops[0])
        elif mode == 'rel':
            t = ops[0] if ops[0] < 0x80 else ops[0]-0x100
            tgt = (ca + 2 + t) & 0xFFFF
            txt = "%s $%02X:%04X" % (mn, b, tgt)
        elif mode == 'rell':
            t = w(); t = t if t < 0x8000 else t-0x10000
            tgt = (ca + 3 + t) & 0xFFFF
            txt = "%s $%02X:%04X" % (mn, b, tgt)
        elif mode == 'abs': txt = "%s $%04X" % (mn, w())
        elif mode == 'absx': txt = "%s $%04X,X" % (mn, w())
        elif mode == 'absy': txt = "%s $%04X,Y" % (mn, w())
        elif mode == 'ind': txt = "%s ($%04X)" % (mn, w())
        elif mode == 'indx': txt = "%s ($%04X,X)" % (mn, w())
        elif mode == 'indl': txt = "%s [$%04X]" % (mn, w())
        elif mode == 'bm': txt = "%s $%02X,$%02X" % (mn, ops[0], ops[1])
        elif mode in ('absl','abslx'):
            v = ops[0] | ops[1]<<8 | ops[2]<<16
            txt = "%s $%06X%s" % (mn, v, ",X" if mode=='abslx' else "")
        out.append((pc, b, ca, data[pc:pc+sz], txt))
        # track m/x
        if mn == 'REP':
            if ops[0] & 0x20: m = 0
            if ops[0] & 0x10: x = 0
        elif mn == 'SEP':
            if ops[0] & 0x20: m = 1
            if ops[0] & 0x10: x = 1
        pc += sz
    return out

if __name__ == '__main__':
    rom = open(sys.argv[1],'rb').read()
    s = int(sys.argv[2],16); e = int(sys.argv[3],16)
    mm = int(sys.argv[4]) if len(sys.argv)>4 else 1
    xx = int(sys.argv[5]) if len(sys.argv)>5 else 1
    for pc,b,ca,raw,txt in disasm(rom,s,e,mm,xx):
        print("%06X  %02X:%04X  %-12s %s" % (pc,b,ca,raw.hex().upper(),txt))

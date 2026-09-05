# Memory map and patch sites

## ROM identity

    2,097,152 bytes, LoROM / SlowROM, ROM+RAM+battery, 8 KiB SRAM
    header $7FB0, "WONDROUS MAGIC", checksum $136A / $EC95
    CRC32 4FFD52A0

## Data

| ROM | What |
|---|---|
| `$081519` | dialogue engine entry (`$90:9519`) |
| `$081675` | `$E0-$FF` extended glyph table |
| `$0A8000` | Japanese font, 448 glyphs, 16×16 2bpp |
| `$0AB000` | kanji half of the same sheet |
| `$08D023-$08D08E` | block E — status screen layout, bank `$91` |
| `$090000-$090EF6` | block C — menus, config, status |
| `$0908A9`, `$0908EE`, `$09095F` | block C tables, 24-bit `$12:xxxx` — party names, classes, nameplates |
| `$090A5E` | block C spell table, 41 × 16-bit `$92:xxxx` |
| `$090F00` | block A pointer table, 297 × 16-bit `$92:xxxx`, targets end `$092FD3` |
| `$0912C0-$092FDF` | block A — items, spells, equipment |
| `$0930F7` | block D pointer table, 51 × 16-bit `$92:xxxx` |
| `$09316E-$093943` | block D — Rinkle's area hints |
| `$093943-$0976C5` | map data, not text |
| `$098000-$09833F` | block B pointer table, 416 × 16-bit displacement from `$098000` |
| `$098340-$0A5625` | block B — story script |
| `$0AF000` | LZSS block — UI icons |
| `$0B3D68` | LZSS chain — 2 nameplate blocks then 7 of world map terrain |
| `$132000` | RUX archive — intro poem and prologue |
| `$152000` | LZSS block — battle font, 128 × 16×16 katakana |
| `$153000-$153179` | battle monster names, 63 × 6 glyph indices |
| `$141000-$141272` | system strings — title, name entry, save/load |
| `$1F0EE7-$1F8000` | free, 28,953 bytes |
| `$0868C9-$087FFF` | free in bank `$90`, 5,943 bytes |
| `$1366E5-$140000` | free, 39,195 bytes |
| `$0976C5-$098000` | free, 2,363 bytes — block D packs its overflow here |
| `$0A5626-$0A8000` | free, 10,714 bytes — inside block B's addressable window |

Block A used to be listed as `$0912C0-$0976C5`. It is not: the item text stops at
`$092FDF` and its table only reaches `$092FD3`. Everything past that is map data
with one island of script in it, the hints at `$09316E`. Walking the whole range
as text invents thousands of phantom strings, which is what made the workbook
2,884 rows instead of 920.

## RAM

| Address | What |
|---|---|
| `$7E:18A8-$18BF` | dialogue engine direct page (`D = $1800`) |
| `$7E:18B9` | unused by the engine, but the battery target cursor writes it |
| `$7E:2000` | shared text layer, 32×32 words |
| `$7E:2C00` | dialogue cell descriptors, 16×16 words |
| `$7E:2DE0` | tilemap staging row (row 15 of the above) |
| `$7E:2E00-$31FF` | glyph staging for DMA |
| `$7E:3208` | name pointer table, 24-bit entries |
| `$7E:3280` | hero name, script bytes |
| `$7F:1DE7-$C374` | decompressed RUX archive |

## Patch sites

### Dialogue engine → half-width (`build/hw_patch.py`)

| Site | Was | Now |
|---|---|---|
| `$90:95CB` | `LDA #$00` | `LDA #$01` — space becomes a text cell |
| `$90:9608` | `PHA / AND #$11` | `JMP $E900` |
| `$90:96CC` | `JSR $9841` | `JSR NEWNL` |
| `$90:9777` | `JSR $9859` | `JSR NEWARG` |
| `$90:99F9` | `AND #$0011` | `AND #$0001` |
| `$90:9A6B` | `LDA $2C00,X` | `JMP NEWUP` |
| `$90:9ACB` | `LDA $2C00,X / AND #$FC00` | `JMP HIATTR` |
| `$90:9738` | `JSR $986A` | `JSR CLOSE` — close a half-open cell first |
| `$90:970B` | `JSR $986A` | `JSR CLOSE` |
| `$90:97E9` | `ADC #$A2` | `ADC #$10` — digits were the Japanese font's base |
| `$91:D033`, `$91:D077` | `$D9` | `$2F` — status separator, full-width slash |

336 bytes of new code at `$086900` (`$90:E900`).

### Intro crawl (`build/prologue_patch.py`)

| Site | Was | Now |
|---|---|---|
| `$A6:881B` | `$15` | `$27` — glyph source bank |
| `$A6:883A` | `$15` | `$27` |

`$A6:880E` has exactly one caller, the crawl driver at `$A6:87FB`, so changing its
font bank affects nothing else.

### Pointer tables rewritten at build time

| Table | Entries | Form | Written by |
|---|---|---|---|
| `$098000` | 416 | 16-bit displacement from `$098000`, carry selects bank `$93`/`$94` | `build/blockb.py` |
| `$0930F7` | 51 | 16-bit absolute `$92:xxxx` | `build/blockd.py` |

Blocks B and D are repacked rather than written in place, so their strings can be
any length. Blocks A, C and E keep their original lengths.

### Build output

    $007FDC   header checksum
    $081608   engine hooks
    $086900   engine code
    $098346   opening dialogue scene
    $0A8022   Latin single letters (text bank)
    $0AB000   Latin letter pairs (kanji bank)
    $13081B   crawl font bank
    $132000   re-encoded RUX archive
    $138000   crawl pair font
    $141020   system strings
    $1F1000   half-width ASCII font

## Debugging notes

- The engine executes from bank `$10`, not `$90`. Breakpoint addresses are
  `10xxxx`, entered flat with no colon.
- Its direct page is `$1800`. A variable disassembled as `$AE` is `$7E:18AE`.
- At `$10:9543` the script pointer is in `A` (bank) and `X` (offset), not `DB:Y` —
  `DB` and `Y` only become the pointer a few instructions later.
- `MVN $7F,$7F` at `$7F:004B` is a RAM-resident block-move trampoline. Breakpoints
  land there constantly; press Out to find the real caller.
- `MVN $7E,$7E` at `$00:183A` is the same idea for WRAM, and it is the long-match
  copy inside the LZSS decompressor. It fires constantly for the same reason.
- There are **two copies of the LZSS decompressor**. `$90:877A` uses zero page
  `$30-$38`; `$02:D1D9` uses `$00-$08` and is what battle code calls. A
  breakpoint on one will never catch the other, which cost a lot of time.
- Savestate layout, for diffing (bsnes-plus, uncompressed): WRAM at file offset
  `$21C`, VRAM at `$3021C`. Anchor WRAM by finding the hero name at `$7E:3280`.
- The tile viewer renders everything at 4bpp. 2bpp assets — the Japanese font,
  the battle font — are invisible noise until you switch it to 2bpp.

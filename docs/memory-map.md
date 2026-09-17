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
| `$090EF6` | item table, 150 × (name, description) 16-bit `$92:xxxx` pairs, item IDs `$00-$95` |
| `$091152` | unidentified-item table, 90 more pairs, all pointing at the three `？？？` items |
| `$0912BA-$092FDF` | block A — items, spells, equipment |
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

It also starts six bytes earlier than it was once given, at `$0912BA`: the
unidentified weapon's name `？？？` and the head of its description sit there,
reached only through the unidentified-item table. Starting at `$0912C0` left
that name in Japanese, and a full-width `？` drawn by the half-width engine is
an `X` - the "XX" in the drop message.

## Items

Item ID `n` is entry `n` of the table at `$090EF6`. Engine-side:

| Where | What |
|---|---|
| `$2A:8000` | item data, 32 bytes per item, index `ID - 1` (ROM `$150000`) |
| `$29:D000` | monster data, 192 bytes per monster, 16-bit fields (ROM `$14D000`) |
| `$7E:32C0` | the party bag, 60 item IDs |
| `$7E:0770` | carried items, `member * 9 + slot`; `$0728` is the same shape, equipped |
| `$81:8000` | field item effects, called from `$90:DA03`; table `$81:8090` |
| `$81:8493` | battle item use; table `$81:85B1`, indexed `ID - $23` |
| `$81:8508` | battle consumption: removes a copy **from the bag** if there is one, and only empties the carried slot when there is not |
| `$91:C7DD` | field item use; table `$11:C82E`. Carry out = consumed, then `$10:DBC6` (bag) or `$10:DC59` (carried) removes it |
| `$80:97B6` | battle effect table, indexed by `$084E`: 0 Fire, 1 Frost, `$08` poison, `$0F` Death, `$10` Thunder, `$11` Quake |

A battle handler sets `$0804` to 1 when the item is used up, 0 when it is not, or
2 when it turns into the item in `$0802` (Magic Seed). `$081x-$086x` is battle
scratch that half the battle code writes, `$084E` included.

`$81:8508` is why an item used in battle can look unconsumed: with a spare in the
bag, the spare goes and the carried one stays. That is the original game.

Death (`$80:BB32`) never calls the poison effect (`$80:D32B`). What it does to a
monster depends on the monster's field `$24`: below 3 it goes straight to
`$DE98` with type 5, which kills unless field 9 is 999. At 3, 4 and 5+ it goes
to `$D861`, `$D8F2` and `$D97F` instead, which hand a status value to `$DCF9`;
that applies up to three effects through `$DE98` by type. Which statuses those
are - whether a resistant monster comes away poisoned - is not traced yet.

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
| `$90:97C6` | `JSR $9859 / CLC / ADC $01,S / SEC / SBC #$08 / JSR $965D` | `JSR NUMPAD` — a number field is `width` cells again, and one that outgrows it flows as text |
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

### Name entry cursor (`build/systext.py`)

| Site | Was | Now |
|---|---|---|
| `$82:A5A3` | `JSR $A73D` | `JSR $F600` — skip the blank chart cells |
| `$82:A5A6` | `JSR $A73D` | `JSR $F600` |

142 bytes of new code at `$017600` (`$02:F600`), after the monster-name routine at
`$02:F500` and inside the same free tail of the bank. `$82:A73D` and `$82:A78B`
are left in place, with nothing calling them. See `docs/screens.md`.

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

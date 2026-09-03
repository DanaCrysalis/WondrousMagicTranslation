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
| `$090000-$090EF6` | block C — menus, config, status |
| `$090F00` | block A pointer table, 283 × 16-bit, bank `$92` |
| `$0912C0-$0976C5` | block A — items, spells, equipment |
| `$098340-$0A5625` | block B — story script |
| `$132000` | RUX archive — intro poem and prologue |
| `$141000-$141272` | system strings — title, name entry, save/load |
| `$1F0EE7-$1F8000` | free, 28,953 bytes |
| `$0868C9-$087FFF` | free in bank `$90`, 5,943 bytes |
| `$1366E5-$140000` | free, 39,195 bytes |

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
| `$90:9ACB` | `LDA $2C00,X / AND #$FC00` | `LDA #$2C00` |

336 bytes of new code at `$086900` (`$90:E900`).

### Intro crawl (`build/prologue_patch.py`)

| Site | Was | Now |
|---|---|---|
| `$A6:881B` | `$15` | `$27` — glyph source bank |
| `$A6:883A` | `$15` | `$27` |

`$A6:880E` has exactly one caller, the crawl driver at `$A6:87FB`, so changing its
font bank affects nothing else.

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

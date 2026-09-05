# Consolidating onto the spreadsheet

The pipeline used to run one way: English lived in `build/script_a.py`,
`script_b.py`, `script_c.py`, `systext.py` and `prologue_patch.py`, and
`tools/make_spreadsheet.py` generated the workbook from them. That meant five
places to edit and a workbook that was a report rather than a source.

It now runs the other way. `data/Wondrous_Magic_script.xlsx` is the script.
`build/sheet.py` reads it and hands the build the same dicts it used to import.

## Apply

    cp sheet.py                     build/sheet.py
    cp build.py                     build/build.py
    cp systext.py                   build/systext.py
    cp prologue_patch.py            build/prologue_patch.py
    cp refresh_spreadsheet.py       tools/refresh_spreadsheet.py
    cp check_script.py              tools/check_script.py
    cp translating.md               docs/translating.md
    cp Wondrous_Magic_script.xlsx   data/Wondrous_Magic_script.xlsx

    git rm build/script_a.py build/script_b.py build/script_c.py
    git rm tools/make_spreadsheet.py
    git rm data/block_b_todo.txt          # block B is complete; it was stale anyway

    pip install openpyxl                  # now a build dependency, not a tool one

Then:

    python3 tools/check_script.py
    python3 build/build.py

`check_script.py` needs the ROM and the workbook and takes a second.
`build/build.py` is the real test — it fits the dictionary and asserts every byte
budget. Nothing here has been run against a ROM, because there isn't one in the
repo, so treat the first build as the actual verification.

## What moved where

| Was | Is now |
|---|---|
| `script_b.TEXT`, `script_c.TEXT` | `Script` sheet, English column |
| `script_a.NAMES` | `Item names` sheet |
| `script_a.TAILS` | `Descriptions` sheet |
| `script_a.build()` | `sheet.block_a()`, unchanged logic |
| `systext.STRINGS` | `Title screen` sheet |
| `systext.CHART_ROWS` | `Name entry` sheet |
| `prologue_patch.POEM` / `.PROLOGUE` | `Intro crawl` sheet |
| `make_spreadsheet.GLOSSARY` | `Glossary` sheet, authored |
| `make_spreadsheet.py` | `tools/refresh_spreadsheet.py`, preserving |

`NAMES` and `TAILS` were checked to round-trip through the workbook byte for
byte, so block A should assemble to exactly what it did before.

## Two things this costs you

**Diffs.** An `.xlsx` is a zip of XML; `git diff` on it says "binary files
differ" and a merge conflict in one is unpleasant. If that starts to hurt, the
cheap fix is a text mirror committed alongside — have `refresh_spreadsheet.py`
also dump `data/script.tsv`, review that in PRs, and keep the workbook as the
editing surface. Worth doing before more than one person edits it.

**Block A stays half-generated.** Its English column in `Script` is assembled,
not authored, because the icon runs have to be copied out of the original ROM
strings and the name padding depends on the Japanese width. Flattening it into
plain rows would make the workbook uniform but would break the link from an item
name to its description, so item renames would silently stop propagating. Kept
the assembly; marked the cells grey.

## Also worth knowing

`data/block_b_todo.txt` was stale — 154 of its 398 entries were already
translated. Block B is now complete except `$098340`, two bytes of `0D 00` with
no text in it. If you want a to-do list in future, filter the `Script` sheet on
an empty English column rather than keeping a separate file that can drift.

# Consolidating onto the spreadsheet

The pipeline used to run one way: English lived in `build/script_a.py`,
`script_b.py`, `script_c.py`, `systext.py` and `prologue_patch.py`, and
`tools/make_spreadsheet.py` generated the workbook from them. That meant five
places to edit and a workbook that was a report rather than a source.

It now runs the other way. `data/Wondrous_Magic_script.ods` is the script.
`build/sheet.py` reads it and hands the build the same dicts it used to import.

## Also worth knowing

The workbook is `.ods` now, not `.xlsx` — see `build/book.py`. The dependency is
`odfpy` rather than `openpyxl`, and `tools/refresh_spreadsheet.py` rewrites the
whole document rather than editing cells in place, so every sheet it does not
generate is read and re-emitted.

**Diffs.** An `.ods` is a zip of XML; `git diff` on it says "binary files
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

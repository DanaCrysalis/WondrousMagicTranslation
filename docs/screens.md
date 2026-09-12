# Title screen and name entry

These do not use the dialogue engine. `$10:9543` never fires on either. They run
off a **shared text layer**, and the intro crawl over the title uses a third
renderer again — three independent text systems in one game.

## The text layer

`$7E:2000`, 32×32 words, one word per 8-pixel cell:

    bit 15        needs redrawing
    bits 10-14    attribute (palette, priority, flip)
    bits 0-9      glyph code

Glyphs are 16×16, so they occupy even cells of even rows — effectively a 16×16
grid. `$82:DBA9` scans the whole buffer, and for any entry with bit 15 set clears
the flag and draws it. `$82:BD68` turns a code into a font address; `$82:B711`
DMAs one 8×8 tile.

Code space is the Japanese font as one flat sheet:

    $000-$0BF     text bank
    $0C0-$1BF     kanji bank
    $1C0+         other symbol banks ($02:8640, $05:28xx)
    $300+         control

## Strings

ROM `$141000` (`$A8:9000`), 16-bit words, **stored value = code + 1**, `$0000`
terminates. The off-by-one is why searching for these strings by code, byte or
word all come up empty — `$82:C1C2` reads the word and immediately `DEC`s it.

    $A8:9020  はじめから            $A8:9098  は い
    $A8:902E  つづきから            $A8:90A2  いいえ
    $A8:903C  そのほか              $A8:90AC  どこに？
    $A8:9048  なまえを入力して下さい。 $A8:9264  いいですか？
    $A8:9064  データをうつす        $A8:90B8  hiragana chart
    $A8:9076  データを消す          $A8:918E  katakana chart
    $A8:9086  なまえを変える

Each chart page is **one** string with rows separated by control `$30D`, and
three symbol codes parked at the ends of the last two rows. They are the buttons,
and the string keeps them verbatim because `$82:A67F` dispatches on the code it
reads back out of the text layer:

    $206   delete   row 6, column 0    $82:A6A5 -> $82:A621, the backspace
    $207   space    row 7, column 1    $82:A6B7, substitutes $BF, stored as $20
    $205   end      row 7, column 0    $82:A6C7, returns $FFFF, name accepted

Column counts from the **right**: the screen cell is `$1C - 2*col`, because the
kana chart read right to left. The row sits at `row*2 + $0A`.

Those three are not in `$0A8000`. `$82:BE9A` resolves codes `$200`-`$209` to bank
`$28` at `$8C00`, in the same interleaved 16×16 layout the text font uses, so
index `code - $1FB` addresses them.

Decoded original in `data/system_strings.txt`.

## Names

Confirming a name stores a 24-bit pointer to `$7E:3280` in the table at
`$7E:3208`, and the name itself at `$7E:3280` as script bytes, `$00` terminated.
The dialogue engine's `$02` control reads that pointer and prints through the
normal renderer.

**Stored byte = chart cell code + `$20`.** Verified against a savestate: a name of
three あ, chart code `$01`, stored as `21 21 21`.

That is what makes the English conversion work without touching any code. Set the
text bank so code `c` draws ASCII `c + $20`; the chart cell then stores `c + $20`,
and the dialogue engine renders script byte `b` as ASCII `b`. Type "Dana", get
"Dana".

## English build

Nothing but these screens reads `$0A8000` any more, so both halves were
repurposed:

    $001-$05E    single Latin letter, code = ASCII - $20     name entry chart
    $0C0-$1BF    two half-width letters                       menus and prompts

Single letters for the chart because each cell is one selectable character; pairs
for prose because a 16×16 cell fits two and the strings then take the same number
of cells as the Japanese did.

Every string is rewritten inside its original byte length and padded, so the table
does not move. `build/systext.py`.

The three buttons are redrawn rather than recoded — three 4×5 letters stepped down
the diagonal, SPC, DEL and END, because three letters will not fit across sixteen
pixels side by side.

## The cursor and the blank cells

The cursor is a palette swap on the cell it sits on, so on a blank one there is
nothing to recolour and it vanishes. The Japanese chart had three such cells and
the game skipped them in `$82:A73D`, a hard-coded list — row 5 is empty, rows 1
and 3 have a hole at column `$0C` — that `$82:A5A3` calls twice, after the move
and before the cursor is redrawn. The English chart has forty-three of them, so
the list does not survive.

`build/systext.py` replaces it with the same idea driven off the screen. The new
routine at `$02:F600` reads the code under the cursor through `$02:BEE5` and
`$02:C40A`, exactly as `$82:A681` does, and while it is not something the chart
put there keeps stepping the way the d-pad was pushed — the same arithmetic as
the move itself at `$82:A52D`-`$A577`, so a continued walk cannot drift from the
step that started it. Both `JSR $A73D` are repointed at it.

Somewhere to sit is a whitelist: a single letter, `$001`-`$05E`, or one of the
three buttons. Not "not blank" — row 5's entry in the chart string is empty, so
nothing is ever written to those cells and what the text layer holds there is
whatever the screen was cleared to.

The chart is therefore the only thing that decides where the cursor can rest, and
editing the `Name entry` sheet cannot strand it. The step budget of sixteen only
exists so that a chart with a wholly blank row cannot hang the game.

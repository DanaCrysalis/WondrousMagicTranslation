# Handoff prompt — block B translation

Paste everything below the line into a new conversation, and attach:

- `data/block_b_todo.txt` — the Japanese still to translate
- `build/script_b.py` — the format, plus the 13 scenes already done
- `data/Wondrous_Magic_script.xlsx` — glossary sheet, for reference

---

I am translating the Super Famicom game *Wondrous Magic* (ワンドラスマジック,
ASCII / System Sacom, 1993) into English. The ROM hacking is finished — engine,
fonts, compression and insertion all work, and the opening scenes are already in
English and playable. What remains is the writing.

Your job is the translation itself. Do not worry about the ROM; work only in the
text format below.

## What I am attaching

`block_b_todo.txt` holds the 398 story strings still in Japanese. Each entry
looks like:

    === 09891C  budget 82 bytes
    クルエル
    「アリアの都の 魔法院へ
     勉強しに いくんだって？
    <WAIT>「あそこの先生は、
     わかくて きれいだけど…
     勉強はキビシイらしいぞ。

`script_b.py` shows the output format and the house style — read the scenes in it
before starting, and match them.

## What I want back

Python dict entries keyed by ROM offset, in the same shape as `script_b.py`:

    0x09891C:
        "Cruel\n"
        '"Off to study at the magic\n guild in Aria, are you?\n'
        '<WAIT>"The teacher there is young\n and lovely, they say...\n'
        " but strict as they come.",

Work through the file in offset order. Give me a few thousand characters of
output at a time and stop; I will come back for more. Do not skip strings, and
do not summarise — every string needs a full translation.

## Hard constraints

**Tokens.** Anything in `<>` is an engine command. Keep every one, in order.

    <NAME:0001>   the hero's name, chosen by the player
    <WAIT>        wait for a button press
    <PAGE>        clear the box to a fresh page
    <C08:07>      scene continue
    <NUM7:xxxx>   a number the engine prints
    <Sxx> <Exx>   icons and window frame pieces

**Line width: 28 characters.** The box is four rows. Put the speaker name alone
on the first line, then at most three lines before the next `<WAIT>`. A fifth
line scrolls the first off the top.

**ASCII only.** No curly quotes, no em dashes, no accents, no ellipsis
character. Use `"` for 「, `...` for …, `-` for dashes. Leading spaces on
continuation lines are meaningful — keep the single space the Japanese uses.

**Budget.** English must fit the byte budget shown. Dictionary compression gives
a lot of headroom, but as a rule of thumb keep the English under about 1.5x the
Japanese character count. If a line will not fit, tighten the wording rather than
dropping content. Flag anything you genuinely cannot fit.

## Names and terms

Established already; use these exactly.

| Japanese | English |
|---|---|
| リンクル | Rinkle — the grandfather, court mage |
| シリア | Silia — the hero's dead mother |
| グナス | Gunas — the hero's missing father |
| ソルディック | Soldic — court swordsman |
| シーラ | Sheila — teacher at the magic guild |
| アルダン王 | King Aldan |
| チャル | Charl — the pet |
| サダ / クルエル / セグ / ネル / リナ | Sada / Cruel / Seg / Nel / Rina |
| シュレル | Shrell — the goddess |
| イヴァス | Ivuas — god of the phantom beasts |
| フレディア, ガストール, ガスタック, ピリオド, セシリア | Fredia, Gastor, Gastack, Period, Cecilia |
| アリアの都 | the city of Aria |
| ダーレス | Darles |
| クローグ | Kroag |
| ネクストリア | Nextria |
| 幻獣 | phantom beast |
| 魔法院 | magic guild |
| 魔法使い | mage |
| 戦士 | warrior |
| 巫女 | priestess |
| 呪文 | spell |
| 祈願 / 祈願力 | prayer |
| 体力 | health |
| ローズコーツ | Rose Coat |
| ベゼッタ / オニキス | Bezetta / Onyx (currencies) |
| ブラッドストーン | Bloodstone |

## Voice

Natural English that reads well, not a gloss. Keep the register distinct:

- **Rinkle** is old and fond — slightly archaic, "Aye", "Hm", "there is no
  helping it". Never modern slang.
- **The hero** is a girl of sixteen: direct, warm, a bit impatient.
- **Sheila** is composed and a touch formal.
- **King Aldan** is stately.
- Villagers are plain and friendly.

Japanese ellipses do a lot of work in this script — they carry hesitation and
grief. Keep them, as `...` or `......`, rather than smoothing them away.

Where a line is a menu prompt or a system message rather than dialogue, render it
plainly and short.

Ask me if a line is ambiguous rather than guessing at plot you cannot see.

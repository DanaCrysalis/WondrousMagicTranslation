#!/usr/bin/env python3
"""Block C - menus, config windows, status text, place names, spells.

ROM $090000-$090EF6, 138 strings. Keys are ROM offsets; values are the English
text in the same token notation `wmtool.text()` produces.

Two kinds of space matter here:

    ' '       half-width, one script byte $7F        prose
    '\\u3000'  full-width, one whole cell, byte $20   window padding

Window rows are 16 cells wide: a left frame piece, 14 cells of content, a right
frame piece, then full-width padding. Half-width English is half a cell per
letter, so content has to come out to a whole number of cells - pad menu columns
to an even character count.

Strings are written in place and must fit their original byte length.
"""

TEXT = {
    # ---- main menu window -------------------------------------------------
    0x09049C:
        "<C06:03><C07:00040F0E>\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\n"
        "\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\n"
        "\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\n"
        "\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\n"
        "<EE8><EE9><EE9><EE9><EE9><EE9><EE9><EE9><EE9><EE9><EE9><EE9><EF9>\u3000\u3000\u3000\n"
        "<EEA>Status     Reorder    <EFA>\u3000\u3000\u3000\n"
        "<EEA>Use Item   Cast Spell <EFA>\u3000\u3000\u3000\n"
        "<EEA>Equip Item Equip Spell<EFA>\u3000\u3000\u3000\n"
        "<EEA>Equip Arms Battle Set <EFA>\u3000\u3000\u3000\n"
        "<EEA>Drop Item  Sound      <EFA>\u3000\u3000\u3000\n"
        "<EFD><EFE><EFE><EFE><EFE><EFE><EFE><EFE><EFE><EFE><EFE><EFE><EFF>\u3000\u3000\u3000\n"
        "<C07:01090E0D>",

    # ---- battle config ----------------------------------------------------
    0x09057E:
        "<C06:03><C07:00040F0E>\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\n"
        "\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\n"
        "\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\n"
        "\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\n"
        "\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\n"
        "<EE8><EE9><EE9><EE9><EE9><EE9><EE9><EE9><EE9><EE9><EE9><EE9><EE9><EE9><EE9><EF9>\n"
        "<EEA>Leader change               <EFA>\n"
        "<EEA>    Auto        Manual      <EFA>\n"
        "<EEA>Party AI                    <EFA>\n"
        "<EEA>    Off         On          <EFA>\n"
        "<EFD><EFE><EFE><EFE><EFE><EFE><EFE><EFE><EFE><EFE><EFE><EFE><EFE><EFE><EFE><EFF>\n"
        "<C07:010A0E0D>",

    # ---- sound config -----------------------------------------------------
    0x090646:
        "<C06:03><C07:00040F0E>\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\n"
        "\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\n"
        "\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\n"
        "\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\n"
        "\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\n"
        "\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\n"
        "\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\n"
        "<EE8><EE9><EE9><EE9><EE9><EE9><EE9><EE9><EE9><EE9><EE9><EE9><EE9><EE9><EE9><EF9>\n"
        "<EEA>Sound mode                  <EFA>\n"
        "<EEA>    Stereo      Mono        <EFA>\n"
        "<EFD><EFE><EFE><EFE><EFE><EFE><EFE><EFE><EFE><EFE><EFE><EFE><EFE><EFE><EFE><EFF>\n"
        "<C07:010C0E0D>",

    # ---- status and shop labels ------------------------------------------
    0x0907DE: "<C09:050C>Next Lv<NUM7:0505>",
    0x0907ED: "<C09:0206>Use Item",
    0x0907F9: "<C09:0206>Cast Spell",
    0x090805: "<C09:0206>Equip Item",
    0x090812: "<C09:0206>Equip Spell",
    0x09081F: "<C09:0206>Drop Item",
    0x09082A: "None",
    0x090831: "<C07:05090E09><C09:0509>Gold<NAME:0801><NUM7:0505>",
    0x090846: "<C07:01050606><C09:0105>Gold\n<NAME:0801><NUM7:0505>",
    0x09085C: "<C07:01080609><C09:0108>Price\n<NAME:0801><NUM7:0505>",
    0x090871: "<C09:0D07>KO",
    0x090879: "<C09:0D07>Stn",
    0x090881: "<C09:0D07>Psn",

    # ---- party ------------------------------------------------------------
    0x0908C6: "Rinkle",
    0x0908CB: "Soldic",
    0x0908D2: "Fredia",
    0x0908D8: "Gastor",
    0x0908DE: "Gastack",
    0x0908E4: "Period",
    0x0908E9: "Cecilia",

    # ---- classes ----------------------------------------------------------
    0x090908: "Apprentice",
    0x090910: "Enchanter",
    0x090918: "Arch Enchanter",
    0x090923: "Wizard",
    0x090929: "Master Wizard",
    0x090933: "Priest",
    0x090939: "Cleric",
    0x09093F: "High Cleric",
    0x090947: "Paladin",
    0x09094D: "Undead Hunter",
    0x090957: "Pickpocket",

    # ---- places -----------------------------------------------------------
    # The map nameplate holds ten half-width characters. "Cruel's house" is
    # thirteen and wrapped a stray letter onto the next line, so the houses use a
    # manufactured glyph, <G80>, drawn in build/glyphs.py.
    0x0909A0: "Tavern",
    0x0909A5: "Barracks",
    0x0909AA: "Inn",
    0x0909B1: "Rest house",
    0x0909B8: "Appraiser",
    0x0909BF: "Antiquary",
    0x0909C8: "Sundries",
    0x0909CF: "Diviner",
    0x0909D6: "Guild",
    0x0909DD: "Library",
    0x0909E4: "Park",
    0x0909E9: "Old port",
    0x0909EE: "Temple",
    0x0909F3: "Palace",
    0x0909F8: "Mayor",
    0x0909FD: "Elder's <G80>",
    0x090A03: "Townsman 1",
    0x090A0A: "Townsman 2",
    0x090A11: "My <G80>",
    0x090A16: "Sada's <G80>",
    0x090A1C: "Void manor",
    0x090A23: "Labyrinth",
    0x090A2B: "Mage tower",
    0x090A33: "Cruel's <G80>",
    0x090A3A: "Matt's <G80>",
    0x090A41: "Clair's <G80>",
    0x090A48: "Gadan's <G80>",
    0x090A4F: "Corp's <G80>",
    0x090A56: "Mel's <G80>",

    # ---- spells -----------------------------------------------------------
    0x090AB4: "Fire",
    0x090AB9: "Fire      Lev.<NUM7:0901> <S34>-<NUM7:0A01>\n"
              " Calls up flame and hurls\n it at a phantom beast.",
    0x090AEB: "Frost",
    0x090AF0: "Frost     Lev.<NUM7:0901> <S34>-<NUM7:0A01>\n"
              " Calls up ice and hurls\n it at a phantom beast.",
    0x090B22: "Thunder",
    0x090B27: "Thunder   Lev.<NUM7:0901> <S34>-<NUM7:0A01>\n"
              " Calls down lightning on\n a phantom beast.",
    0x090B57: "Quake",
    0x090B5D: "Quake     Lev.<NUM7:0901> <S34>-<NUM7:0A01>\n"
              " Raises an earthquake\n during battle.",
    0x090B8C: "Death",
    0x090B8F: "Death     Lev.<NUM7:0901> <S34>-<NUM7:0A01>\n"
              " Deals death to a\n phantom beast.",
    0x090BBB: "Boost",
    0x090BC0: "Boost     Lev.<NUM7:0901> <S34>-<NUM7:0A01>\n"
              " Raises the party's power\n during battle.",
    0x090BF2: "Shell",
    0x090BF6: "Shell     Lev.<NUM7:0901> <S34>-<NUM7:0A01>\n"
              " Wards off some damage from\n phantom beasts in battle.",
    0x090C2C: "High Speed",
    0x090C33: "High SpeedLev.<NUM7:0901> <S34>-<NUM7:0A01>\n"
              " Quickens the party\n during battle.",
    0x090C62: "Hold",
    0x090C67: "Hold      Lev.<NUM7:0901> <S34>-<NUM7:0A01>\n"
              " Stops a phantom beast\n from moving in battle.",
    0x090C9A: "Chaotic",
    0x090CA0: "Chaotic   Lev.<NUM7:0901> <S34>-<NUM7:0A01>\n"
              " Confuses a phantom beast\n during battle.",
    0x090CCC: "Silence",
    0x090CD2: "Silence   Lev.<NUM7:0901> <S34>-<NUM7:0A01>\n"
              " Seals away all magic\n during battle.",
    0x090D03: "Heal",
    0x090D07: "Heal      Lev.<NUM7:0901> <S33>-<NUM7:0A01>\n"
              " Restores the health of\n one party member.",
    0x090D3B: "Cure",
    0x090D3F: "Cure      Lev.<NUM7:0901> <S33>-<NUM7:0A01>\n"
              " Restores the party's\n condition.",
    0x090D70: "Recover",
    0x090D76: "Recover   Lev.<NUM7:0901> <S33>-<NUM7:0A01>\n"
              " Restores the health of\n the whole party.",
    0x090DAB: "Balance",
    0x090DB0: "Balance   Lev.<NUM7:0901> <S33>-<NUM7:0A01>\n"
              " Shares health evenly\n across the whole party.",
    0x090DE2: "Resurrect",
    0x090DE8: "Resurrect Lev.<NUM7:0901> <S33>-<NUM7:0A01>\n"
              " Revives one fallen\n party member.",
    0x090E19: "Drain",
    0x090E1E: "Drain     Lev.<NUM7:0901> <S33>-<NUM7:0A01>\n"
              " Drains health from a\n phantom beast in battle.",
    0x090E4E: "Wish",
    0x090E54: "Wish      Lev.<NUM7:0901> <S33>-<NUM7:0A01>\n"
              " Prays to the goddess in\n battle and is answered.",
    0x090E88: "Recall",
    0x090E8D: "Recall    Lev.<NUM7:0901> <S33>-<NUM7:0A01>\n"
              " Returns you to the mouth\n of the labyrinth.",
    0x090EC3: "Fade",
    0x090EC8: "Fade      Lev.<NUM7:0901> <S33>-<NUM7:0A01>\n"
              " Keeps phantom beasts from\n crossing your path.",
}

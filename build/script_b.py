#!/usr/bin/env python3
"""Block B - the story script.

ROM $098340-$0A5625, 412 strings, 42,219 Japanese characters across 4,681 lines.
That is a novel's worth of dialogue and is being translated in passes; this file
holds what is done. Anything absent is left in Japanese, which the engine renders
as ASCII nonsense - so untranslated scenes are obvious rather than subtly wrong.

Keys are ROM offsets. Values use the token notation `wmtool.text()` produces:

    <NAME:0001>   the hero's name
    <WAIT>        wait for input
    <PAGE>        clear to a new page
    <C08:07>      the engine's scene-continue call

The window is 14 cells, so **28 half-width characters per line**. Four text rows
per box; a fifth line scrolls the first away. Keep the speaker on its own line,
then at most three lines before a <WAIT>.
"""

TEXT = {
    # ---- prologue: the promise -------------------------------------------
    0x098342:
        "<NAME:0001>\n"
        '"Grandpa, where are my\n mum and dad?\n'
        "<WAIT><PAGE>Rinkle\n"
        '"<NAME:0001>, do not be sad.\n'
        '<WAIT>"Your mother Silia died\n soon after your birth,\n'
        " of a sickness no one\n could name...\n"
        "<WAIT><PAGE><NAME:0001>\n"
        '"She died?\n'
        "<WAIT><PAGE>Rinkle\n"
        '"...Aye.\n'
        "<WAIT><PAGE><NAME:0001>\n"
        '"Then Papa too?\n Is he dead as well?\n'
        "<WAIT><PAGE>Rinkle\n"
        '"Perhaps he is...\n'
        '<WAIT><C08:07>"Your father Gunas left on\n a journey the day after\n'
        " she died, all of a\n sudden...\n"
        "<WAIT><PAGE><NAME:0001>\n"
        '"A journey? Why?\n'
        "<WAIT><PAGE>Rinkle\n"
        '"I never learned. Only that\n he said: I must go to\n'
        " Darles. Then he was gone.\n"
        '<WAIT>"That was the last of it.\n'
        "<WAIT><PAGE><NAME:0001>\n"
        '"Then he may still be\n alive!\n'
        '<WAIT><C08:07>"I am going to Darles too!\n To look for Papa!!\n'
        "<WAIT><PAGE>Rinkle\n"
        '"You shall not!\n'
        '<WAIT>"A child as small as you\n would be eaten on the road\n'
        " by a phantom beast.\n"
        "<WAIT><PAGE><NAME:0001>\n"
        '"I am going anyway!\n I want to! I want to!\n'
        "<WAIT><PAGE>Rinkle\n"
        '"There is no helping it...\n'
        '<WAIT>"When you turn 16 and are\n grown, shall we go to\n'
        " Darles together, you\n and I?\n"
        "<WAIT><PAGE><NAME:0001>\n"
        '"Yes!\n'
        '<WAIT>"16... let me see...\n Ten more birthdays and\n'
        " then I can go.\n It is a promise, Grandpa!\n"
        "<WAIT><PAGE>Rinkle\n"
        '"Aye, a promise!\n You truly are an honest,\n'
        " clever girl...\n"
        '<WAIT>"I look forward to what\n you will become...\n'
        "<WAIT><PAGE>",

    # ---- setting out ------------------------------------------------------
    0x0985E8:
        "Rinkle\n"
        '"<NAME:0001>, are you ready\n for the journey?\n'
        "<WAIT><PAGE><NAME:0001>\n"
        '"Yes... nearly.\n'
        '<WAIT>"...Grandpa?\n'
        "<WAIT><PAGE>Rinkle\n"
        '"Hm? What is it?\n'
        "<WAIT><PAGE><NAME:0001>\n"
        '"We are only going to Darles\n to look for Father.\n'
        '<WAIT>"So why must I study\n magic first?\n'
        "<WAIT><PAGE>Rinkle\n"
        '"Hm. Well now.\n'
        '<WAIT>"Out that way the phantom\n beasts are nothing like\n'
        " the ones about here.\n They swarm, and they are\n"
        " terrible.\n"
        '<WAIT>"Without proper magic it is\n far too dangerous to\n'
        " travel at all.\n"
        "<WAIT><PAGE><NAME:0001>\n"
        '"I see......\n'
        '<WAIT>"We will find Father,\n won\'t we?\n'
        '<WAIT>"We go to Darles, we find\n him, and the three of us\n'
        " come straight home again.\n Won't we?\n"
        '<WAIT>"I love this village. Being\n away from Rina and all my\n'
        " friends for a long time -\n"
        '<WAIT>"I should hate it......\n'
        "<WAIT><PAGE>Rinkle\n"
        '"Hm......\n'
        '<WAIT>"Then the sooner you learn\n your magic, the sooner we\n'
        " can reach Darles.\n"
        '<WAIT>"That is how it must be.\n'
        "<WAIT><PAGE><NAME:0001>\n"
        '"All right......\n'
        "<WAIT><PAGE>Rinkle\n"
        '"Now then. Are you ready?\n'
        "<WAIT><PAGE><NAME:0001>\n"
        '"Yes.\n'
        '<WAIT>"Come along, Charl...\n Stand about there and we\n'
        " shall leave without you!\n"
        "<WAIT><PAGE>Charl\n"
        '"Kyui!\n'
        "<C08:07><WAIT><PAGE>Rinkle\n"
        '"...<NAME:0001>, we go!\n First to the city of Aria!',

    0x09884B: 'Rinkle\n"Shall we rest a while...',

    0x098863:
        "Sada\n"
        '"Oh my... are you leaving\n already?\n'
        '<WAIT>"Here, take this with you...\n It is wine of my own\n'
        " making.\n"
        '<WAIT>"Good for drinking on the\n road...\n'
        '<WAIT>"If you mean to drink it in\n a fight, mind you equip it\n'
        ' under "Equip Item" first,\n or it will not serve.\n'
        '<WAIT>"Do take care of yourself.',

    0x098907: 'Sada\n"Do take care of yourself.',

    0x09891C:
        "Cruel\n"
        '"Off to study at the magic\n guild in Aria, are you?\n'
        '<WAIT>"The teacher there is young\n and lovely, they say...\n'
        " but strict as they come.",

    0x09896E: 'Cruel\n"I wish I had been born a\n mage myself...',

    0x09898F:
        "Seg\n"
        '"<NAME:0001>, are you off\n already?\n'
        "<WAIT><PAGE><NAME:0001>\n"
        '"Yes......\n'
        "<WAIT><PAGE>Seg\n"
        '"With the two of you gone\n we shan\'t dare so much as\n'
        " scrape a knee.\n"
        '<WAIT>"Your medicines have saved\n us more often than I can\n'
        " count.\n"
        "<WAIT><PAGE><NAME:0001>\n"
        '"It will be all right,\n Uncle Seg.\n'
        '<WAIT>"Every medicine the village\n needs is with the headman\n'
        " now...\n"
        '<WAIT>"Ask him whenever you have\n need of one.\n'
        "<WAIT><PAGE>Seg\n"
        '"Is that so. Well then,\n that is one weight off me.\n'
        "<WAIT><PAGE>Nel\n"
        '"...Take care, then, Master\n Rinkle. And you,\n'
        " <NAME:0001>.\n"
        "<WAIT><PAGE><NAME:0001>\n"
        '"I will.\n'
        "<WAIT><PAGE>Rina\n"
        '"..............\n'
        '<WAIT>"<NAME:0001>...\n Do your best out there!\n'
        "<WAIT><PAGE><NAME:0001>\n"
        '"...Thank you.\n'
        "<WAIT><PAGE>Rina\n"
        '"Keep well, <NAME:0001>.\n'
        "<WAIT><PAGE><NAME:0001>\n"
        '"You too, Rina.\n'
        "<WAIT><C08:07><WAIT><PAGE>Rinkle\n"
        '"Shall we be off then...\n <NAME:0001>?\n'
        "<WAIT><PAGE><NAME:0001>\n"
        '"......Yes.',

    # ---- the palace at Aria ----------------------------------------------
    0x098B2E:
        "Rinkle\n"
        '"Your Majesty, it has been\n a long while. This is my\n'
        " granddaughter,\n <NAME:0001>.\n"
        "<WAIT><PAGE><NAME:0001>\n"
        '"How do you do.\n'
        "<WAIT><PAGE>King Aldan\n"
        '"You have come a long way.\n Well met, Lord Rinkle.\n'
        '<WAIT>"Lord Rinkle, court mage.\n Soldic, court swordsman.\n'
        " And... Gunas...\n"
        '<WAIT>"With those three, this city\n of Aria stood the\n'
        " strongest in the land...\n"
        '<WAIT>"And now only Soldic\n remains...\n'
        "<WAIT><PAGE>Rinkle\n"
        '"In a world as peaceful as\n this one, being strongest\n'
        " counts for little.\n"
        "<WAIT><PAGE>King Aldan\n"
        '"That is true enough...\n'
        "<WAIT><PAGE>Rinkle\n"
        '"Then we shall take our\n leave. I will call again\n'
        " if anything should arise.",

    0x098C74:
        "King Aldan\n"
        '"Lord Rinkle, court mage.\n'
        '"Soldic, court swordsman.\n'
        "<WAIT> And... Gunas...\n"
        '<WAIT>"With those three, this city\n of Aria stood the\n'
        " strongest in the land...",

    # ---- the magic guild --------------------------------------------------
    0x098CDB:
        "Sheila\n"
        '"Welcome to the guild.\n'
        '<WAIT>"It has been a long while,\n Lord Rinkle. And this is\n'
        " your granddaughter.\n"
        "<WAIT><PAGE><NAME:0001>\n"
        '"How do you do.\n'
        "<WAIT><PAGE>Sheila\n"
        '"My dear, you are the very\n image of Silia!\n'
        "<WAIT><PAGE><NAME:0001>\n"
        '"Of my mother!?\n'
        "<WAIT><PAGE>Sheila\n"
        '"Silia was a truly splendid\n mage...\n'
        '<WAIT>"I am sure you will make a\n fine one yourself...\n'
        '<WAIT>"Well then, let us begin\n your study at once.\n'
        "<WAIT><PAGE><NAME:0001>\n"
        '"......Yes.\n'
        "<WAIT><PAGE><C08:07>Sheila\n"
        '"Magic has two halves.\n Spells, which call on fire\n'
        ' and water to fell phantom\n beasts,\n'
        '<WAIT>"and prayers, which heal\n those who have been hurt.\n'
        '<WAIT>"A spell costs you health.\n A prayer costs you prayer.\n'
        '<WAIT>"And then......\n   .\n   .\n   .\n'
        "<WAIT><PAGE><C08:07><EE9><EE9>And so <NAME:0001> sat\n"
        "through her lessons, and\n learned a handful of\n"
        "new spells.\n"
        "<WAIT><PAGE><C08:07><PAGE><NAME:0001>\n"
        '"Phew. My head is full!\n Is there more?\n'
        "<WAIT><PAGE>Sheila\n"
        '"We shall stop there for\n now...\n'
        "<WAIT><PAGE><NAME:0001>\n"
        '"Is that the end?\n'
        "<WAIT><PAGE><C08:07>Sheila\n"
        '"You will sit an\n examination.\n'
        "<WAIT><PAGE><NAME:0001>\n"
        '"What!\n'
        "<WAIT><PAGE>Sheila\n"
        '"North of Aria there is a\n town called Kroag.\n'
        '<WAIT>"In its tower of magic lies\n a jewel called the\n'
        " Rose Coat.\n"
        '<WAIT>"Bring that jewel back and\n you have passed.\n'
        "<WAIT><PAGE><NAME:0001>\n"
        '"...... So I only have to\n fetch a jewel from the\n'
        " tower at Kroag?\n"
        "<WAIT><PAGE>Sheila\n"
        '"Of course it is not only\n that.\n'
        '<WAIT>"All manner of phantom\n beasts have been called\n'
        " into that tower.\n"
        '<WAIT>"You will face them alone,\n with the magic you have\n'
        " just learned.\n"
        '<WAIT>"And when the Rose Coat is\n in your hands, you will\n'
        " be a true mage at last.\n"
        "<WAIT><PAGE><NAME:0001>\n"
        '"A... alone? On my own?\n'
        "<WAIT><PAGE>Sheila\n"
        '"Naturally. It is an\n examination.\n'
        '<WAIT>"Lord Rinkle, please see\n <NAME:0001> on her way.',

    0x0990B0: 'Sheila\n"The Rose Coat is in the\n tower of magic at Kroag.',

    0x0990CF: "The magic guild is closed.",
}

# ---------------------------------------------------------------------------
# System and map text. These are the recurring messages - signposts, item and
# battle results, shops, the inn, the temple, saving - so they are worth far
# more per byte than any single scene. Leading full-width spaces (\u3000) are
# kept where the original centres a menu, because the cursor is drawn at a fixed
# cell and half-width padding would shift it.
SYSTEM = {
    0x0990CF: "The magic guild is closed.",
    0x09956E: "The tavern has none of its\nusual life today.\n"
              "<WAIT>...The man who is always\nhere is asleep.",
    0x099682: "Two or three people in the\npark are talking of a dragon\nseen in the forest.",
    0x0996B0: "Stepping into the park puts\nyou in mind of the village.",
    0x09A1B7: "The door said to be the\nmouth of the labyrinth is\nshut fast.",
    0x09A1D9: "The hall has fallen to ruin.",
    0x09A444: "The palace is closed.",
    0x09E818: "The mouth of the labyrinth\nthat runs through to Kroag.",
    0x0A17D2: "\u3000\u3000\u3000\u3000\u3000\u3000\u3000<EF8>\n Ahead: Sheloon village",
    0x0A17EB: "<EF3> gives you a hint about\nthe game.",
    0x0A1ACF: "\u3000\u3000\u3000\u3000\u3000\u3000\u3000<EF0>\n\u3000\u3000\u3000Aria, just ahead",
    0x0A1AE7: "You cannot go on ahead\nwithout Grandpa.",
    0x0A1AFF: "<EF5> opens camp mode.\n"
              "<WAIT>Hold <EF6> while walking to\nmove more quickly.",
    0x0A1B41: "Rinkle has\nvanished...",
    0x0A1B54: "Remember. You have a power\nof your own.\n"
              "<WAIT>A strange power, granted\nby the goddess...",
    0x0A1C3F: "\u3000\u3000\u3000Tower of Magic\n\u3000\u3000\u3000\u3000Entrance",
    0x0A1DBB: "\u3000\u3000\u3000\u3000\u3000Tower of Souls\n\u3000\u3000\u3000\u3000\u3000\u3000Entrance",
    0x0A1F45: "Oh? The dwarf seems to have\nhidden something away.",
    0x0A302C: "A great mirror stands here.\nLooking into it clears your\nheart. Prayer restored.",
    0x0A30BE: "\n Come no nearer this tower",
    0x0A31A8: "Enter, if you want treasure.\nThough none leave alive...",
    0x0A3C68: "\u3000\u3000When the goddess's mage\n\u3000comes to this place\n\u3000the way shall open",
    0x0A554E: "\u3000\u3000Is there not something\n\u3000\u3000\u3000left undone...?",

    # ---- items and effects ------------------------------------------------
    0x0A3CA9: "That item cannot be used.",
    0x0A3CB9: "The Beast Feather returns\n you to the entrance.",
    0x0A3CD7: "The <NAME:0301> is lit.\n It carries Fade's effect.",
    0x0A3CF6: "The <NAME:0301> goes out.\n The effect of Fade ends.",
    0x0A3D17: "Who?",
    0x0A3D1D: "<NAME:0201> recovers\n <NUM7:0501>% of health.",
    0x0A3D3A: "<NAME:0201> recovers\n one rank of condition.",
    0x0A3D57: "Nothing is wrong with\n <NAME:0201>.",
    0x0A3D6E: "<NAME:0201> is revived.",
    0x0A3D8A: "Using the <NAME:0301>.",
    0x0A3D98: "<NAME:0201> recovers\n all prayer.",
    0x0A3DB6: "<NAME:0201> does not\n have that ability.",
    0x0A3DCE: "<NAME:0201> loses\n all prayer......",
    0x0A3DED: "<NAME:0201> recovers\n all health.",
    0x0A3E08: "The fallen are revived, and\nthose who were not have\nfallen......",
    0x0A3E37: " The Pendulum\n  begins to spin.",
    0x0A3E4F: "It became a <NAME:0301>",
    0x0A3E5C: "Found <NUM7:0501> Bezetta.",
    0x0A3E6C: "A <NUM7:0501> came up.\n\n<EE9><EE9>Nothing wrong, I hope...?",
    0x0A3E8A: "\u3000\u3000\u3000\u3000A <NUM7:0501>......?\n\n<EE9><EE9>Nothing wrong, I hope...?",
    0x0A3EA9: "<NAME:0201> cannot use it",
    0x0A3EB7: "Experience rose by 1.",
    0x0A3EC9: "Balance was cast.",
    0x0A3ED9: "<NAME:0201> has\nfallen.",
    0x0A3EF5: "The whole party recovers\nall condition and health.",
    0x0A3FDB: "Bubbles everywhere......",
    0x0A3FF2: "There is money inside.",
    0x0A4000: "<NAME:0201> raises magic\n by <NUM7:0501>.",
    0x0A401B: "<NAME:0201> raises\n defence by 5.",
    0x0A4034: "Your Bezetta is changed\ninto Onyx.",
    0x0A404F: "Your Onyx is changed\ninto Bezetta.",
    0x0A406A: "Opening the Beast Box.",
    0x0A407C: "The Float Stone returns you\n to the entrance.",
    0x0A41E1: "That spell cannot be used.",
    0x0A41F1: "Casting <NAME:0401>.",
    0x0A41FF: "On whom?",
    0x0A4205: "Not enough prayer.",
    0x0A4214: "Not enough health.",
    0x0A4221: "<NAME:0201> has\nfallen.",
    0x0A4235: "<NAME:0201> has turned\nto stone.",

    # ---- inventory --------------------------------------------------------
    0x0A424B: "Drop something from the bag?\n\u3000\u3000\u3000\u3000\u3000Yes\n\u3000\u3000\u3000\u3000\u3000No",
    0x0A426E: "Dropping the <NAME:0301>.\n\u3000\u3000\u3000\u3000\u3000Yes\n\u3000\u3000\u3000\u3000\u3000No",
    0x0A428D: "\u3000\u3000\u3000That item must not\n\u3000\u3000be thrown away!",
    0x0A42A6: '\u3000\u3000Wear that one through\n\u3000\u3000"Equip Weapon"\n\u3000\u3000instead.',
    0x0A42CE: "\u3000\u3000The bag is full - you\n\u3000\u3000cannot unequip.",
    0x0A42EC: " Found\n the <NAME:0301>.",
    0x0A42FE: "<WAIT> But the bag is full and you\n can carry nothing more.",
    0x0A431F: " Found\n <NUM7:0501> Bezetta.",
    0x0A4333: " Found\n <NUM7:0501> Onyx.",
    0x0A4347: " It is locked.",
    0x0A4356: " Using the Chest Key.\n<WAIT>",
    0x0A436A: " Using the\n\u3000\u3000\u3000\u3000Magic Key.\n<WAIT>",
    0x0A4386: " It is locked.",
    0x0A4395: "\u3000\u3000Use the Door Key?\n\u3000\u3000\u3000\u3000Yes\n<WAIT>\u3000\u3000\u3000\u3000No",
    0x0A43C1: " Using the\n\u3000\u3000\u3000\u3000Magic Key.",
    0x0A43DC: " Using the\n\u3000\u3000\u3000\u3000Goddess Key.",

    # ---- battle results ---------------------------------------------------
    0x0A43F8: "\u3000A phantom beast appears!",
    0x0A4407: " The party felled the beast\nand gained <NUM7:0501> experience.",
    0x0A4429: "\u3000\u3000\u3000\u3000\u3000And then,\n<NUM7:0501> Onyx was found",
    0x0A4444: "Obtained the <NAME:0301>",
    0x0A4453: "\u3000\u3000\u3000\u3000\u3000\u3000\u3000was obtained.",
    0x0A4466: "\n<NAME:0101>\n\u3000\u3000\u3000\u3000has gained a level!",
    0x0A447E: "Learned <NAME:0401> Lev.<NUM7:0901>!",
    0x0A448D: "Health rose by <NUM7:0501>",
    0x0A449C: "Attack rose by <NUM7:0501>",
    0x0A44AD: "Defence rose by <NUM7:0501>",
    0x0A44BE: "Magic rose by <NUM7:0501>",
    0x0A44CD: "Prayer rose by <NUM7:0501>",
    0x0A44DE: "<NAME:0001> and the others\n\u3000have run out of strength.\n"
              "The goddess did not hear<EE9><EE9>",

    # ---- the appraiser ----------------------------------------------------
    0x0A4509: "\u3000\u3000This is the appraiser.",
    0x0A4518: "\u3000\u3000What can I do for you?\n\u3000\u3000\u3000\u3000\u3000Appraise\n\u3000\u3000\u3000\u3000\u3000Change",
    0x0A453D: "<PAGE>\u3000\u3000Which shall I look at?",
    0x0A454D: "Look at the <NAME:0301>?\n\u3000\u3000\u3000\u3000\u3000\u3000Yes\n\u3000\u3000\u3000\u3000\u3000\u3000No",
    0x0A456E: "You can tell what that is\nyourself, surely?",
    0x0A457F: "\u3000\u3000Which way round?\n\u3000\u3000Bezetta<EF0>Onyx\n\u3000\u3000Onyx<EF0>Bezetta",
    0x0A45A7: " That will be\n 50 Bezetta<EE9><EE9>",
    0x0A45BE: "......Hm,\nthis is a <NAME:0301>.",
    0x0A45D1: " ...You are short of money.",
    0x0A4626: "\u3000\u3000How much shall I change?",
    0x0A467B: "\u3000\u3000That is settled then?\n\u3000\u3000\u3000\u3000\u3000Yes\n\u3000\u3000\u3000\u3000\u3000No",
    0x0A469A: "\u3000\u3000\u3000\u3000\u3000Much obliged.",

    # ---- the antiquary ----------------------------------------------------
    0x0A46DF: "\u3000\u3000This is the antiquary.",
    0x0A46F1: "\u3000\u3000What can I do for you?\n\u3000\u3000\u3000\u3000\u3000\u3000Buy\n\u3000\u3000\u3000\u3000\u3000\u3000Sell",
    0x0A4715: "\u3000\u3000Buy with which?\n\u3000\u3000\u3000\u3000Bezetta\n\u3000\u3000\u3000\u3000Onyx",
    0x0A4738: " What are you looking for?",
    0x0A4748: " Which will you sell me?",
    0x0A4759: "Sell the <NAME:0301>?\n\u3000\u3000\u3000\u3000\u3000\u3000Yes\n\u3000\u3000\u3000\u3000\u3000\u3000No",
    0x0A477B: "\u3000\u3000\u3000Thank you kindly.\n\n\u3000\u3000Anything else?",
    0x0A4795: "\u3000\u3000\u3000Hmm......!\n You are short of money!?",
    0x0A47AE: "\u3000\u3000\u3000Much obliged.\n\n\u3000\u3000Anything else?",
    0x0A47C6: "\u3000\u3000I cannot buy that.",

    # ---- the sundries shop ------------------------------------------------
    0x0A47D7: "Welcome to my shop!",
    0x0A47EA: " What can I get you?\n\u3000\u3000\u3000\u3000\u3000\u3000Buy\n\u3000\u3000\u3000\u3000\u3000\u3000Sell",
    0x0A480E: "\u3000\u3000Buy with which?\n\u3000\u3000\u3000\u3000Bezetta\n\u3000\u3000\u3000\u3000Onyx",
    0x0A4831: "What are you looking for?",
    0x0A4840: "Which will you sell me?",
    0x0A4850: "Sell the <NAME:0301>?\n\u3000\u3000\u3000\u3000\u3000\u3000Yes\n\u3000\u3000\u3000\u3000\u3000\u3000No",
    0x0A4872: "\u3000\u3000Thank you kindly.\n\n\u3000\u3000\u3000Anything else?",
    0x0A488C: "\u3000\u3000\u3000\u3000\u3000Oh dear?\n Are you short of money?",
    0x0A48A5: "\u3000\u3000Thank you kindly.\n\n\u3000\u3000\u3000Anything else?",
    0x0A48BF: "\u3000\u3000I cannot buy that.",

    # ---- lodging and saving -----------------------------------------------
    0x0A490E: "That is 40 Bezetta each,\nso <NUM7:0501> Bezetta\nfor the lot.",
    0x0A4937: "Short of Bezetta, are you?\n...Then I shall take\n<NUM7:0501> Onyx.",
    0x0A495D: "No Onyx either...\n...I am sorry, but then\nI am afraid not.",
    0x0A4982: "...You have thought better\nof it. Do call again.",
    0x0A499E: "<C07:010B0E0D><PAGE> Save your data?\n\u3000\u3000\u3000\u3000\u3000\u3000Yes\n\u3000\u3000\u3000\u3000\u3000\u3000No",
    0x0A49C7: " Save to which slot?",
    0x0A49D5: "\u3000\u3000What would you like?\n\u3000\u3000\u3000\u3000\u3000Store\n\u3000\u3000\u3000\u3000\u3000Collect",
    0x0A49F8: "\u3000\u3000Which will you store?",
    0x0A4A06: " The room is full - there\n is nowhere left to put it.",
    0x0A4A24: "\u3000\u3000Which will you collect?",
    0x0A4A35: " Your bag is full.\n You can carry nothing more.",
    0x0A4A54: "The <NAME:0301>, then.",
    0x0A4A5F: "\n\u3000\u3000You have stored nothing.",
    0x0A4A70: "\n\u3000\u3000Your bag is empty.",

    # ---- the temple -------------------------------------------------------
    0x0A4A81: "\u3000\u3000\u3000This is the temple.",
    0x0A4A90: "How may we serve you?\n\u3000\u3000\u3000Pray\n\u3000\u3000\u3000Heal\u3000\u3000Revive",
    0x0A4AB8: " Your prayer is already\n full.",
    0x0A4AD3: "Oh? Your offering falls\na little short......",
    0x0A4AEC: "Who?",
    0x0A4AF2: "<NAME:0201> is in no\nneed of healing......",
    0x0A4B10: "Who?",
    0x0A4B16: "\u3000\u3000<NAME:0201> is\n\u3000\u3000\u3000\u3000\u3000quite well.",
    0x0A4B31: "\u3000\u3000We shall heal them.",
    0x0A4B41: "The offering is\n<NUM7:0501> Bezetta.",
    0x0A4BB0: "\u3000\u3000We shall revive them.",

    # ---- the inn ----------------------------------------------------------
    0x0A4BC0: "\u3000\u3000This is the inn.\n<WAIT>\u3000\u3000Staying the night...?\n\u3000\u3000\u3000\u3000\u3000\u3000Yes\n\u3000\u3000\u3000\u3000\u3000\u3000No",
    0x0A4BF2: "That is 40 Bezetta each,\nso let me see...\n<NUM7:0501> for the lot.",
    0x0A4C19: "Oh! Short of money, are you?",
    0x0A4C2A: "Short of Bezetta?!\nNothing for it - <NUM7:0501>\nOnyx will do instead.",
    0x0A4C53: "No Onyx either...\n...I am sorry, but\nanother time.",
    0x0A4C73: "...Oh, you have changed your\n mind. Do come again.",
}

TEXT.update(SYSTEM)

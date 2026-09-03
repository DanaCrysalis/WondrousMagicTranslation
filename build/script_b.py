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

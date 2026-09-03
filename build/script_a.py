#!/usr/bin/env python3
"""Block A - items, weapons, armour and their descriptions.

ROM $0912C0-$092FDF: 151 items, each a short name string followed by a
description string. The description's first line repeats the name, padded, then
carries stat icons (`<S36>` `<S37>` `<S38>`) and their values; the rest is the
usage or equip restriction.

Only two tables are written by hand - NAMES and TAILS. The descriptions are
assembled: the English name padded to the same cell width the Japanese name and
its padding occupied, then the icon run copied verbatim, then the English tail.
113 distinct tails cover all 151 descriptions.
"""

NAMES = {
    "？": "?",
    "？？？": "???",
    "スターリング": "Sterling",       "銀の短剣": "Silver Dagger",
    "ライトソード": "Light Sword",    "ルナリング": "Luna Ring",
    "銀の長剣": "Silver Sword",       "メイス": "Mace",
    "木の杖": "Wooden Staff",         "マギスタッフ": "Magi Staff",
    "メタルワンド": "Metal Wand",     "魔法の杖": "Magic Staff",
    "ローブ": "Robe",                 "ケープ": "Cape",
    "魔法のローブ": "Magic Robe",     "魔法のケープ": "Magic Cape",
    "魔法のコート": "Magic Coat",     "レザーアーマ": "Leather Armour",
    "フルチェイン": "Full Chain",     "ライトアーマ": "Light Armour",
    "プレート": "Plate",              "フルプレート": "Full Plate",
    "シールド": "Shield",             "銅の盾": "Copper Shield",
    "鉄の盾": "Iron Shield",          "魔法の盾": "Magic Shield",
    "革の帽子": "Leather Cap",        "魔法の帽子": "Magic Hat",
    "バトルハット": "Battle Hat",     "ヘルメット": "Helmet",
    "フルヘルム": "Full Helm",        "革の靴": "Leather Shoes",
    "魔法の靴": "Magic Shoes",        "鉄のブーツ": "Iron Boots",
    "銅のブーツ": "Copper Boots",     "ガントレット": "Gauntlet",
    "アミュレット": "Amulet",         "ペンダント": "Pendant",
    "タリスマン": "Talisman",         "チャイム": "Chime",
    "プリズム": "Prism",              "幻獣の羽": "Beast Feather",
    "アワーグラス": "Hourglass",      "ルナグラブ": "Luna Glove",
    "メテオストン": "Meteor Stone",   "女神のひかり": "Goddess Light",
    "魔力の杖": "Mana Staff",         "神殿のカギ": "Temple Key",
    "フード": "Hood",                 "キュアハーブ": "Cure Herb",
    "ブドウ酒": "Wine",               "ポーション": "Potion",
    "マンドラゴラ": "Mandragora",     "魔法の指輪": "Magic Ring",
    "創世の木": "World Tree",         "杖の小羽": "Staff Feather",
    "杖の大羽": "Staff Plume",        "シーホルン": "Sea Horn",
    "マーブル": "Marble",             "ロザリオ": "Rosary",
    "宝箱のカギ": "Chest Key",        "トビラのカギ": "Door Key",
    "毒の長剣": "Poison Sword",       "魔法の剣": "Magic Sword",
    "魔法の大剣": "Magic Greatsword", "ベガソード": "Vega Sword",
    "テラソード": "Terra Sword",      "悪を召す杖": "Staff of Evil",
    "巫女の杖": "Priestess Staff",    "サタンロッド": "Satan Rod",
    "イビルワンド": "Evil Wand",      "ルナスタッフ": "Luna Staff",
    "スターロッド": "Star Rod",       "シュレルの杖": "Shrell's Staff",
    "ルナローブ": "Luna Robe",        "スターローブ": "Star Robe",
    "魔法の鎧": "Magic Mail",         "ベガアーマー": "Vega Armour",
    "テラアーマー": "Terra Armour",   "女神の盾": "Goddess Shield",
    "ベガシールド": "Vega Shield",    "テラシールド": "Terra Shield",
    "クラウン": "Crown",              "ルナハット": "Luna Hat",
    "スターハット": "Star Hat",       "ベガメット": "Vega Helm",
    "テラメット": "Terra Helm",       "ルナサンダル": "Luna Sandals",
    "ルナシューズ": "Luna Shoes",     "星のシューズ": "Star Shoes",
    "ベガブーツ": "Vega Boots",       "テラブーツ": "Terra Boots",
    "ベガグローブ": "Vega Gloves",    "テラグローブ": "Terra Gloves",
    "魔法のマント": "Magic Mantle",   "死神のマント": "Reaper Mantle",
    "黒いマント": "Black Mantle",     "ベガマント": "Vega Mantle",
    "テラマント": "Terra Mantle",     "ローズコーツ": "Rose Coat",
    "デビルメイス": "Devil Mace",     "ルビー": "Ruby",
    "ブラドストン": "Bloodstone",     "カッパー": "Copper",
    "ゴールド": "Gold",               "アース": "Earth",
    "魔法のピアス": "Magic Earring",  "スカルジェム": "Skull Gem",
    "治癒の指輪": "Healing Ring",     "祈りの指輪": "Prayer Ring",
    "サモンハープ": "Summon Harp",    "ルナブローチ": "Luna Brooch",
    "ベガストーン": "Vega Stone",     "アストラル石": "Astral Stone",
    "王妃の指輪": "Queen's Ring",     "治療の指輪": "Cure Ring",
    "魂の指輪": "Soul Ring",          "女神像": "Goddess Idol",
    "邪神像": "Idol of Evil",         "合格祈願の酒": "Luck Wine",
    "女神のカギ": "Goddess Key",      "悪魔のハート": "Devil Heart",
    "ペンデュラム": "Pendulum",       "魔法のたね": "Magic Seed",
    "お金のなる木": "Money Tree",     "呪いのダイス": "Cursed Dice",
    "ヘルタロット": "Hell Tarot",     "ブルーメダル": "Blue Medal",
    "金のスプーン": "Gold Spoon",     "魔のバイブル": "Evil Bible",
    "女神の呪文書": "Goddess Tome",   "チェンレター": "Chain Letter",
    "女神のピアス": "Goddess Ring",   "バブルパイプ": "Bubble Pipe",
    "夢の宝くじ": "Dream Ticket",     "ルナシンボル": "Luna Symbol",
    "星のあかし": "Star Token",       "悪魔のサイフ": "Devil Purse",
    "ルナソープ": "Luna Soap",        "星のコロン": "Star Cologne",
    "ルナルージュ": "Luna Rouge",     "月の砂": "Moon Sand",
    "星の砂": "Star Sand",            "マジックキー": "Magic Key",
    "幻獣の箱": "Beast Box",          "浮遊石": "Float Stone",
    "星の図鑑": "Star Atlas",         "創世の書": "Genesis Book",
    "意識の書": "Book of Mind",       "マリオネット": "Marionette",
    "−−−−−": "-----",
    " 装備できません。": " Cannot be equipped.",
}

TAILS = {
    " 魔法を使えるものだけが\n 装備できます。":
        " Only those who can use\n magic may equip this.",
    " 戦士だけが装備できます。":
        " Only warriors may equip it.",
    " 魔法使いは装備できません。":
        " Mages cannot equip this.",
    " シュレルの杖の\n 1パーツです。":
        " One piece of\n Shrell's Staff.",
    " 戦士が装備でき、ダメージを\n うけると体力が回復します。":
        " Warriors only. Restores\n health when damage is taken.",
    " 何やら不思議なことが、\n 書いてあります。":
        " Something strange is\n written here.",
    " 女神に祈れる魔法使いだけが\n 装備できます。":
        " Only mages who can pray to\n the goddess may equip it.",
    " 誰でも装備できます。":
        " Anyone may equip this.",
    " 魔法を使えるものは\n 装備できません。":
        " Those who can use magic\n cannot equip this.",
    " 城の戦士と魔法戦士だけが\n 装備できます。":
        " Only palace warriors and\n magic warriors may equip it.",
    " あまり使わないほうが\n いいと思いますけど……。":
        " Best not to use this one,\n I should think......",
    " とくべつな あかしです。":
        " A token of something rare.",
    " 武器のようですが・・・\n 鑑定しないと使えません。":
        " Looks like a weapon...\n Appraise it before use.",
    " 防具のようですが・・・\n 鑑定しないと使えません。":
        " Looks like armour...\n Appraise it before use.",
    " 変な物みつけましたね。\n 効果は全く解りません。":
        " An odd find. Nobody knows\n what it does.",
    " 魔法使いだけが\n 装備できます。":
        " Only mages may equip this.",
    " 魔法戦士だけが装備できる\n 不思議なコートです。":
        " A strange coat only a magic\n warrior may equip.",
    " 城の戦士だけが装備できる\n すぐれた鎧です。":
        " Fine mail only a palace\n warrior may equip.",
    " 魔法戦士だけが装備できる\n 不思議な帽子です。":
        " A strange hat only a magic\n warrior may equip.",
    " 魔法戦士だけが装備できる\n 不思議なブーツです。":
        " Strange boots only a magic\n warrior may equip.",
    " ファイアの魔法が1回だけ\n 使えます。":
        " Casts Fire once.",
    " フロストの魔法が1回だけ\n 使えます。":
        " Casts Frost once.",
    " シェルの魔法が1回だけ\n 使えます。":
        " Casts Shell once.",
    " 1回だけ戦闘から\n ぬけだすことができます。":
        " Escapes from battle once.",
    " ブーストの魔法が1回だけ\n 使えます。":
        " Casts Boost once.",
    " 1回だけ、そのダンジョンの\n 入口にもどれます。":
        " Returns you to the mouth of\n the labyrinth once.",
    " ハイスピードの魔法が1回\n だけ使えます。":
        " Casts High Speed once.",
    " シュレルの杖を復活させる\n ことができます。":
        " Can restore Shrell's Staff.",
    " クウェイクの魔法が1回だけ\n 使えます。":
        " Casts Quake once.",
    " 移動中、幻獣と出あわなく\n なります。":
        " Keeps phantom beasts from\n crossing your path.",
    " いにしえの神殿を、\n 開くことができます。":
        " Opens the ancient temple.",
    " 体力が1回だけ、\n 60％回復します。":
        " Restores 60% of health,\n once.",
    " 状態を1ランク回復します。":
        " Cures one rank of status.",
    " 状態を1ランク回復し、\n 体力が20％回復します。":
        " Cures one rank of status\n and restores 20% health.",
    " 状態を1ランク回復し、\n 体力が80％回復します。":
        " Cures one rank of status\n and restores 80% health.",
    " 戦闘不能を回復し、\n 体力が全回復します。":
        " Revives the fallen and\n restores all health.",
    " ドラゴノイムをよぶための\n ホルンです。":
        " A horn for calling\n the Dragonoim.",
    " ヴァンパイアをたおすことが\n できるオマモリです。":
        " A charm that can bring\n down a vampire.",
    " 1回だけ宝箱のカギを\n 開けることができます。":
        " Opens a treasure chest\n once.",
    " 1回だけトビラのカギを\n 開けることができます。":
        " Opens a locked door once.",
    " 戦士だけが装備でき、攻撃す\n ると幻獣に毒をあたえます。":
        " Warriors only. Attacks\n poison the phantom beast.",
    " 戦士だけが装備でき、攻撃\n すると幻獣がマヒします。":
        " Warriors only. Attacks\n paralyse the phantom beast.",
    " 戦士だけが装備でき、\n 幻獣を─撃でたおせます。":
        " Warriors only. Fells a\n phantom beast in one blow.",
    " 魔法使いが装備でき、移動中\n に使うと幻獣と戦闘できます":
        " Mages only. Used on the\n move, it calls up a battle.",
    " 巫女だけが装備でき、攻撃す\n るとキュアの効果があります":
        " Priestesses only. Attacks\n carry the effect of Cure.",
    " 魔法を使えるものが装備で\n き、デスの効果があります":
        " For those who use magic.\n Carries the effect of Death.",
    " 魔法を使えるものが装備でき\n サンダーの効果があります。":
        " For those who use magic.\n Carries Thunder's effect.",
    " 魔法使いが装備でき攻撃する\n とフロストの効果があります":
        " Mages only. Attacks carry\n the effect of Frost.",
    " 魔法使いが装備でき攻撃する\n とファイアの効果があります":
        " Mages only. Attacks carry\n the effect of Fire.",
    " 女神の巫女が装備でき、女神\n の力をかりることができます":
        " For priestesses. Borrows\n the power of the goddess.",
    " 魔法使いが装備できダメージ\n が1／2になります。":
        " Mages only. Halves the\n damage taken.",
    " 魔法使いが装備できダメージ\n が1／2、体力が回復します":
        " Mages only. Halves damage\n and restores health.",
    " 戦士が装備でき、ダメージが\n 1／2になります。":
        " Warriors only. Halves the\n damage taken.",
    " 戦士が装備でき、ダメージが\n 1／2、体力が回復します。":
        " Warriors only. Halves damage\n and restores health.",
    " 魔法使いが装備できフロスト\n の攻撃を無効にします。":
        " Mages only. Nullifies\n Frost attacks.",
    " 魔法使いが装備できファイア\n の攻撃を無効します。":
        " Mages only. Nullifies\n Fire attacks.",
    " 戦士が装備でき、フロストの\n 攻撃を無効にします。":
        " Warriors only. Nullifies\n Frost attacks.",
    " 戦士が装備でき、ファイアの\n 攻撃を無効にします。":
        " Warriors only. Nullifies\n Fire attacks.",
    " 巫女だけが装備でき、あるく\n ごとに祈願力が回復します。":
        " Priestesses only. Restores\n prayer as you walk.",
    " 魔法使いが装備できダメージ\n フロアを1／2にします。":
        " Mages only. Halves damage\n from the floor.",
    " 魔法使いが装備できダメージ\n フロアを無効にします。":
        " Mages only. Nullifies\n damage from the floor.",
    " 戦士だけが装備できダメージ\n フロアを1／2にします。":
        " Warriors only. Halves damage\n from the floor.",
    " 戦士だけが装備できダメージ\n フロアを無効にします。":
        " Warriors only. Nullifies\n damage from the floor.",
    " 戦士だけが装備でき、パララ\n イズの攻撃を無効にします。":
        " Warriors only. Nullifies\n paralysing attacks.",
    " 戦士だけが装備できストーン\n の攻撃を無効にします。":
        " Warriors only. Nullifies\n petrifying attacks.",
    " 戦士だけが装備でき、あるく\n ごとに体力が回復します。":
        " Warriors only. Restores\n health as you walk.",
    " 戦士だけが装備でき、\n デスの攻撃を無効にします。":
        " Warriors only. Nullifies\n Death attacks.",
    " 戦士だけが装備できドレイン\n の攻撃を無効にします。":
        " Warriors only. Nullifies\n Drain attacks.",
    " 戦士だけが装備でき、クウェ\n イクの攻撃を無効にします。":
        " Warriors only. Nullifies\n Quake attacks.",
    " エンチャンターの\n シンボルです。":
        " The symbol of\n the Enchanter.",
    " 誰でも装備でき、クウェイク\n の効果があります。":
        " Anyone may equip it. Carries\n the effect of Quake.",
    " ウィザードの\n シンボルです。":
        " The symbol of\n the Wizard.",
    " マスターウィザードの\n シンボルです。":
        " The symbol of the\n Master Wizard.",
    " プリーストの\n シンボルです。":
        " The symbol of\n the Priest.",
    " マスター・クレリックの\n シンボルです。":
        " The symbol of the\n Master Cleric.",
    " 誰でも装備でき、\n サンダーを無効にします。":
        " Anyone may equip it.\n Nullifies Thunder.",
    " 女魔法使いだけが装備でき、\n 経験値がふえていきます。":
        " Only sorceresses may equip\n it. Experience keeps rising.",
    " 誰でも装備でき、ドレインの\n 攻撃を1回だけ無効にします":
        " Anyone may equip it.\n Nullifies one Drain attack.",
    " 誰でも装備でき、あるくごと\n に体力が回復します。":
        " Anyone may equip it. Health\n returns as you walk.",
    " 巫女が装備でき、戦闘中に使\n うと祈願力が回復します。":
        " Priestesses only. Restores\n prayer when used in battle.",
    " 移動中に1回だけ幻獣を\n よび出します。":
        " Calls up a phantom beast\n once, on the move.",
    " 誰でも装備でき、パラライズ\n の攻撃を無効にします。":
        " Anyone may equip it.\n Nullifies paralysing attacks.",
    " 誰でも装備でき、ポイズンの\n 攻撃を無効にします。":
        " Anyone may equip it.\n Nullifies poison attacks.",
    " 誰でも装備でき、ストーンの\n 攻撃を無効にします。":
        " Anyone may equip it.\n Nullifies petrifying attacks.",
    " 誰でも装備でき、使うごとに\n 状態が回復します。":
        " Anyone may equip it. Each\n use restores your condition.",
    " 誰でも装備でき、使うごとに\n 体力が10％回復します。":
        " Anyone may equip it. Each\n use restores 10% health.",
    " 誰でも装備でき、使うごとに\n 戦闘不能を回復します。":
        " Anyone may equip it. Each\n use revives the fallen.",
    " 女神に祈れる魔法使いが装備\n でき、祈願力を全回復します":
        " For mages who pray to the\n goddess. Restores all prayer.",
    " 女神に祈れる魔法使いが装備\n でき、祈願力が全部消えます":
        " For mages who pray to the\n goddess. Drains all prayer.",
    " 1回だけ体力が全回復する\n 不思議なお酒です。":
        " A strange wine. Restores\n all health, once.",
    " 1回だけ とくべつなトビラ\n を開くことができます。":
        " Opens one special door,\n once.",
    " 戦闘不能の人は回復しますが\n 何でもない人は……。":
        " It revives the fallen. For\n anyone else......",
    " 装備していると、宝箱のある\n フロアでは、まわります。":
        " While equipped, it spins on\n floors that hold a chest.",
    " 使うと、何かのアイテムに\n 変化するはずです。":
        " Used, it should turn into\n some other item.",
    " そのとおりのアイテムです。":
        " Exactly what it says it is.",
    " 使うたびに、経験値が\n 上がります。":
        " Each use raises\n your experience.",
    " 使うたびに、バランスの\n 効果があります。":
        " Each use carries the\n effect of Balance.",
    " あまり、使わないほうが\n いいと思いますけど……。":
        " Best not to use this one,\n I should think......",
    " 1回だけ、パーティ全体が\n 全回復します。":
        " Fully restores the whole\n party, once.",
    " 何かの てがみです。":
        " A letter of some kind.",
    " なにか不思議な こえが\n きこえるはずです。":
        " You should hear some\n strange voice in it.",
    " 使ってみれば わかります。":
        " Use it and you will see.",
    " ハズレくじです。":
        " A losing ticket.",
    " お金が中に入っています。":
        " There is money inside.",
    " 女魔法使いだけが使え、\n 魔力が5上がります。":
        " Sorceresses only.\n Raises magic by 5.",
    " 女魔法使いだけが使え、\n 魔力が10上がります。":
        " Sorceresses only.\n Raises magic by 10.",
    " 女魔法使いだけが使え、\n 防力が5上がります。":
        " Sorceresses only.\n Raises defence by 5.",
    " 使うとベゼッタが全部\n オニキスに喚金されます。":
        " Changes all your Bezetta\n into Onyx.",
    " 使うとオニキスが全部\n ベゼッタに換金されます。":
        " Changes all your Onyx\n into Bezetta.",
    " なんどでも、なんでも開いて\n しまう魔法のカギです。":
        " A magic key that opens\n anything, again and again.",
    " 開けると、幻獣が\n 飛び出してきます。":
        " Open it and a phantom\n beast leaps out.",
    " 使うと、リコールの効果が\n あります。":
        " Used, it carries the\n effect of Recall.",
    " 誰でも装備でき、1回だけ\n デスの攻撃を無効にします。":
        " Anyone may equip it.\n Nullifies one Death attack.",
    " 装備できません。": " Cannot be equipped.",
}


import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
import wmtool
import re

START, END = 0x0912C0, 0x092FDF


def build():
    """Walk the block and return {rom offset: English}. Descriptions are
    assembled from the English name, the original icon run, and the tail."""
    out, missing = {}, []
    p = START
    while p < END:
        toks, q = wmtool.decode(p)
        s = wmtool.text(toks).rstrip('\n')
        if not any(ord(c) > 0x2000 for c in s):
            p = q
            continue
        if '\n' not in s:
            if s in NAMES:
                out[p] = NAMES[s]
            else:
                missing.append((p, s))
            p = q
            continue
        head, _, tail = s.partition('\n')
        tail = '\n' + tail
        i = head.find('<S')
        jp_name, icons = (head[:i], head[i:]) if i >= 0 else (head, '')
        en_name = NAMES.get(jp_name.rstrip())
        en_tail = TAILS.get(tail.lstrip('\n') and tail[1:])
        if en_name is None or en_tail is None:
            missing.append((p, s))
            p = q
            continue
        # every rendered Japanese glyph is one whole cell, so the name and its
        # padding are worth twice as many half-width slots. Where an English
        # name will not fit that, the icon run simply shifts left - it only has
        # to stay inside the 14-cell window.
        icons = icons.replace('＋', '+').replace('−', '-').replace('？', '?')
        pad = max(1, 2 * len(re.sub(r'<[^>]*>', '', jp_name)) - len(en_name))
        line = en_name + ' ' * pad + icons
        width = len(re.sub(r'<[^>]*>', '', line)) * 0.5 + line.count('<S')
        if width > 14:
            missing.append((p, 'first line %s cells: %s' % (width, en_name)))
            p = q
            continue
        out[p] = line + '\n' + en_tail
        p = q
    return out, missing

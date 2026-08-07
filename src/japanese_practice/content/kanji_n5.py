"""JLPT N5 kanji seed data.

On'yomi are written in katakana and kun'yomi in hiragana, following the
convention fixed by the content model. Okurigana are shown in parentheses
(e.g. ``大き(い)``). Multiple readings are separated by ``/``.

Categories are the thematic segments defined by the content model:
Numbers & Counting, People & Family, Nature & Weather, Time & Calendar,
Actions, Descriptions, Places.
"""

from __future__ import annotations

from ..models import CharacterSeed

__all__ = ["KANJI_N5"]

_NUMBERS = "Numbers & Counting"
_PEOPLE = "People & Family"
_NATURE = "Nature & Weather"
_TIME = "Time & Calendar"
_ACTIONS = "Actions"
_DESC = "Descriptions"
_PLACES = "Places"


def _k(
    glyph: str,
    meaning: str,
    onyomi: str | None,
    kunyomi: str | None,
    category: str,
    stroke_count: int,
) -> CharacterSeed:
    """Build an N5 kanji seed with the shared script/level fields filled in."""
    return CharacterSeed(
        glyph=glyph,
        script="kanji",
        meaning=meaning,
        onyomi=onyomi,
        kunyomi=kunyomi,
        jlpt_level="N5",
        category=category,
        stroke_count=stroke_count,
    )


KANJI_N5: list[CharacterSeed] = [
    # --- Numbers & Counting -------------------------------------------------
    _k("一", "one", "イチ/イツ", "ひと(つ)", _NUMBERS, 1),
    _k("二", "two", "ニ", "ふた(つ)", _NUMBERS, 2),
    _k("三", "three", "サン", "みっ(つ)", _NUMBERS, 3),
    _k("四", "four", "シ", "よっ(つ)/よん", _NUMBERS, 5),
    _k("五", "five", "ゴ", "いつ(つ)", _NUMBERS, 4),
    _k("六", "six", "ロク", "むっ(つ)", _NUMBERS, 4),
    _k("七", "seven", "シチ", "なな(つ)", _NUMBERS, 2),
    _k("八", "eight", "ハチ", "やっ(つ)", _NUMBERS, 2),
    _k("九", "nine", "キュウ/ク", "ここの(つ)", _NUMBERS, 2),
    _k("十", "ten", "ジュウ/ジッ", "とお", _NUMBERS, 2),
    _k("百", "hundred", "ヒャク", None, _NUMBERS, 6),
    _k("千", "thousand", "セン", "ち", _NUMBERS, 3),
    _k("万", "ten thousand", "マン/バン", None, _NUMBERS, 3),
    _k("円", "yen, circle", "エン", "まる(い)", _NUMBERS, 4),
    _k("半", "half", "ハン", "なか(ば)", _NUMBERS, 5),
    _k("分", "minute, part", "ブン/フン", "わ(ける)/わ(かる)", _NUMBERS, 4),
    _k("何", "what, how many", "カ", "なに/なん", _NUMBERS, 7),
    _k("毎", "every", "マイ", None, _NUMBERS, 6),
    # --- People & Family ----------------------------------------------------
    _k("人", "person", "ジン/ニン", "ひと", _PEOPLE, 2),
    _k("男", "man, male", "ダン/ナン", "おとこ", _PEOPLE, 7),
    _k("女", "woman, female", "ジョ/ニョ", "おんな", _PEOPLE, 3),
    _k("子", "child", "シ/ス", "こ", _PEOPLE, 3),
    _k("父", "father", "フ", "ちち", _PEOPLE, 4),
    _k("母", "mother", "ボ", "はは", _PEOPLE, 5),
    _k("友", "friend", "ユウ", "とも", _PEOPLE, 4),
    _k("先", "ahead, previous", "セン", "さき", _PEOPLE, 6),
    _k("生", "life, birth", "セイ/ショウ", "い(きる)/う(まれる)", _PEOPLE, 5),
    _k("名", "name", "メイ/ミョウ", "な", _PEOPLE, 6),
    _k("口", "mouth", "コウ/ク", "くち", _PEOPLE, 3),
    _k("目", "eye", "モク/ボク", "め", _PEOPLE, 5),
    _k("耳", "ear", "ジ", "みみ", _PEOPLE, 6),
    _k("手", "hand", "シュ", "て", _PEOPLE, 4),
    _k("足", "foot, leg", "ソク", "あし/た(りる)", _PEOPLE, 7),
    # --- Nature & Weather ---------------------------------------------------
    _k("火", "fire", "カ", "ひ", _NATURE, 4),
    _k("水", "water", "スイ", "みず", _NATURE, 4),
    _k("木", "tree, wood", "モク/ボク", "き", _NATURE, 4),
    _k("金", "gold, money", "キン/コン", "かね", _NATURE, 8),
    _k("土", "earth, soil", "ド/ト", "つち", _NATURE, 3),
    _k("山", "mountain", "サン", "やま", _NATURE, 3),
    _k("川", "river", "セン", "かわ", _NATURE, 3),
    _k("天", "heaven, sky", "テン", "あめ/あま", _NATURE, 4),
    _k("気", "spirit, energy", "キ/ケ", None, _NATURE, 6),
    _k("雨", "rain", "ウ", "あめ", _NATURE, 8),
    _k("電", "electricity", "デン", None, _NATURE, 13),
    _k("花", "flower", "カ", "はな", _NATURE, 7),
    _k("空", "sky, empty", "クウ", "そら/あ(く)", _NATURE, 8),
    _k("犬", "dog", "ケン", "いぬ", _NATURE, 4),
    _k("魚", "fish", "ギョ", "さかな/うお", _NATURE, 11),
    _k("鳥", "bird", "チョウ", "とり", _NATURE, 11),
    # --- Time & Calendar ----------------------------------------------------
    _k("日", "day, sun", "ニチ/ジツ", "ひ/か", _TIME, 4),
    _k("月", "month, moon", "ゲツ/ガツ", "つき", _TIME, 4),
    _k("年", "year", "ネン", "とし", _TIME, 6),
    _k("時", "time, hour", "ジ", "とき", _TIME, 10),
    _k("間", "interval, between", "カン/ケン", "あいだ/ま", _TIME, 12),
    _k("今", "now", "コン/キン", "いま", _TIME, 4),
    _k("前", "before, front", "ゼン", "まえ", _TIME, 9),
    _k("後", "after, behind", "ゴ/コウ", "あと/うし(ろ)/のち", _TIME, 9),
    _k("午", "noon", "ゴ", None, _TIME, 4),
    _k("週", "week", "シュウ", None, _TIME, 11),
    _k("曜", "day of the week", "ヨウ", None, _TIME, 18),
    # --- Actions ------------------------------------------------------------
    _k("行", "go", "コウ/ギョウ", "い(く)/おこな(う)", _ACTIONS, 6),
    _k("来", "come", "ライ", "く(る)", _ACTIONS, 7),
    _k("見", "see, look", "ケン", "み(る)", _ACTIONS, 7),
    _k("聞", "hear, ask", "ブン/モン", "き(く)", _ACTIONS, 14),
    _k("話", "speak, story", "ワ", "はな(す)/はなし", _ACTIONS, 13),
    _k("読", "read", "ドク/トク", "よ(む)", _ACTIONS, 14),
    _k("書", "write", "ショ", "か(く)", _ACTIONS, 10),
    _k("買", "buy", "バイ", "か(う)", _ACTIONS, 12),
    _k("食", "eat, food", "ショク", "た(べる)/く(う)", _ACTIONS, 9),
    _k("飲", "drink", "イン", "の(む)", _ACTIONS, 12),
    _k("出", "go out, take out", "シュツ", "で(る)/だ(す)", _ACTIONS, 5),
    _k("入", "enter, put in", "ニュウ", "はい(る)/い(れる)", _ACTIONS, 2),
    _k("立", "stand", "リツ", "た(つ)", _ACTIONS, 5),
    _k("休", "rest", "キュウ", "やす(む)", _ACTIONS, 6),
    _k("学", "study, learning", "ガク", "まな(ぶ)", _ACTIONS, 8),
    _k("会", "meet, association", "カイ/エ", "あ(う)", _ACTIONS, 6),
    _k("帰", "return, go home", "キ", "かえ(る)", _ACTIONS, 10),
    # --- Descriptions -------------------------------------------------------
    _k("大", "big", "ダイ/タイ", "おお(きい)", _DESC, 3),
    _k("小", "small", "ショウ", "ちい(さい)", _DESC, 3),
    _k("高", "tall, expensive", "コウ", "たか(い)", _DESC, 10),
    _k("安", "cheap, peaceful", "アン", "やす(い)", _DESC, 6),
    _k("新", "new", "シン", "あたら(しい)/あら(た)", _DESC, 13),
    _k("古", "old", "コ", "ふる(い)", _DESC, 5),
    _k("長", "long, chief", "チョウ", "なが(い)", _DESC, 8),
    _k("多", "many", "タ", "おお(い)", _DESC, 6),
    _k("少", "few, a little", "ショウ", "すく(ない)/すこ(し)", _DESC, 4),
    _k("早", "early, fast", "ソウ", "はや(い)", _DESC, 6),
    _k("白", "white", "ハク/ビャク", "しろ(い)/しら", _DESC, 5),
    _k("上", "up, above", "ジョウ", "うえ/あ(がる)/のぼ(る)", _DESC, 3),
    _k("下", "down, below", "カ/ゲ", "した/さ(がる)/くだ(る)", _DESC, 3),
    _k("中", "middle, inside", "チュウ", "なか", _DESC, 4),
    _k("右", "right", "ウ/ユウ", "みぎ", _DESC, 5),
    _k("左", "left", "サ", "ひだり", _DESC, 5),
    _k("本", "book, origin", "ホン", "もと", _DESC, 5),
    _k("字", "character, letter", "ジ", "あざ", _DESC, 6),
    _k("語", "language, word", "ゴ", "かた(る)", _DESC, 14),
    # --- Places -------------------------------------------------------------
    _k("東", "east", "トウ", "ひがし", _PLACES, 8),
    _k("西", "west", "セイ/サイ", "にし", _PLACES, 6),
    _k("南", "south", "ナン", "みなみ", _PLACES, 9),
    _k("北", "north", "ホク", "きた", _PLACES, 5),
    _k("国", "country", "コク", "くに", _PLACES, 8),
    _k("校", "school", "コウ", None, _PLACES, 10),
    _k("店", "shop, store", "テン", "みせ", _PLACES, 8),
    _k("駅", "station", "エキ", None, _PLACES, 14),
    _k("道", "road, way", "ドウ", "みち", _PLACES, 12),
    _k("社", "company, shrine", "シャ", "やしろ", _PLACES, 7),
    _k("車", "car, vehicle", "シャ", "くるま", _PLACES, 7),
]

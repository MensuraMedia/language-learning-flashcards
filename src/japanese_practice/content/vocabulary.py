"""Vocabulary sets — whole words rather than single characters.

Extracted from the worksheets in the companion
`language-learning <https://github.com/MensuraMedia/language-learning>`_
repository, which is this project's authority for content:
``japanese/vocabulary/japanese-worksheet-{days,months,numbers,time}-*.pdf``.

These are the first decks whose prompt is a **word**, not a glyph. The engine
needed no change for that — a word is stored in ``glyph`` exactly as a character
is, graded on ``meaning`` the way kanji already were, and carries its reading in
``romaji``. What did change is presentation: 月曜日 and "Wednesday" need more
room on a card than あ and "a" do.
"""

from __future__ import annotations

from ..models import CharacterSeed

__all__ = ["VOCABULARY"]

_DAYS = "Days of the week"
_MONTHS = "Months"
_NUMBERS = "Numbers"
_TIME = "Time"


def _w(glyph: str, romaji: str, meaning: str, category: str) -> CharacterSeed:
    """A vocabulary entry.

    ``script="vocab"`` keeps these out of every kana and kanji query without a
    single one of them needing to know these exist.
    """
    return CharacterSeed(
        glyph=glyph,
        script="vocab",
        romaji=romaji,
        meaning=meaning,
        category=category,
    )


#: 71 entries across four sets.
VOCABULARY: tuple[CharacterSeed, ...] = (
    # -- days of the week ------------------------------------------------
    _w("月曜日", "getsuyoubi", "Monday", _DAYS),
    _w("火曜日", "kayoubi", "Tuesday", _DAYS),
    _w("水曜日", "suiyoubi", "Wednesday", _DAYS),
    _w("木曜日", "mokuyoubi", "Thursday", _DAYS),
    _w("金曜日", "kin'youbi", "Friday", _DAYS),
    _w("土曜日", "doyoubi", "Saturday", _DAYS),
    _w("日曜日", "nichiyoubi", "Sunday", _DAYS),
    # -- months -----------------------------------------------------------
    _w("一月", "ichigatsu", "January", _MONTHS),
    _w("二月", "nigatsu", "February", _MONTHS),
    _w("三月", "sangatsu", "March", _MONTHS),
    _w("四月", "shigatsu", "April", _MONTHS),
    _w("五月", "gogatsu", "May", _MONTHS),
    _w("六月", "rokugatsu", "June", _MONTHS),
    _w("七月", "shichigatsu", "July", _MONTHS),
    _w("八月", "hachigatsu", "August", _MONTHS),
    _w("九月", "kugatsu", "September", _MONTHS),
    _w("十月", "juugatsu", "October", _MONTHS),
    _w("十一月", "juuichigatsu", "November", _MONTHS),
    _w("十二月", "juunigatsu", "December", _MONTHS),
    # -- numbers ----------------------------------------------------------
    _w("零", "rei", "0", _NUMBERS),
    _w("一", "ichi", "1", _NUMBERS),
    _w("二", "ni", "2", _NUMBERS),
    _w("三", "san", "3", _NUMBERS),
    _w("四", "yon", "4", _NUMBERS),
    _w("五", "go", "5", _NUMBERS),
    _w("六", "roku", "6", _NUMBERS),
    _w("七", "nana", "7", _NUMBERS),
    _w("八", "hachi", "8", _NUMBERS),
    _w("九", "kyuu", "9", _NUMBERS),
    _w("十", "juu", "10", _NUMBERS),
    _w("二十", "nijuu", "20", _NUMBERS),
    _w("十一", "juuichi", "21", _NUMBERS),
    _w("三十", "sanjuu", "30", _NUMBERS),
    _w("十二", "juuni", "35", _NUMBERS),
    _w("四十", "yonjuu", "40", _NUMBERS),
    _w("十三", "juusan", "47", _NUMBERS),
    _w("五十", "gojuu", "50", _NUMBERS),
    _w("六十", "rokujuu", "60", _NUMBERS),
    _w("十五", "juugo", "68", _NUMBERS),
    _w("七十", "nanajuu", "70", _NUMBERS),
    _w("十七", "juunana", "74", _NUMBERS),
    _w("八十", "hachijuu", "80", _NUMBERS),
    _w("九十", "kyuujuu", "90", _NUMBERS),
    _w("十九", "juukyuu", "99", _NUMBERS),
    _w("百", "hyaku", "100", _NUMBERS),
    _w("百十", "hyakujuu", "110", _NUMBERS),
    _w("百二十", "hyakunijuu", "120", _NUMBERS),
    _w("百三十", "hyakusanjuu", "130", _NUMBERS),
    _w("百四十", "hyakuyonjuu", "140", _NUMBERS),
    _w("百五十", "hyakugojuu", "150", _NUMBERS),
    _w("百六十", "hyakurokujuu", "160", _NUMBERS),
    _w("百七十", "hyakunanajuu", "170", _NUMBERS),
    _w("百八十", "hyakuhachijuu", "180", _NUMBERS),
    _w("百九十", "hyakukyuujuu", "190", _NUMBERS),
    _w("二百", "nihyaku", "200", _NUMBERS),
    # -- time -------------------------------------------------------------
    _w("時", "ji / toki", "hour / o'clock", _TIME),
    _w("後", "ato / go", "after / PM", _TIME),
    _w("分", "fun / pun", "minute", _TIME),
    _w("朝", "asa", "morning", _TIME),
    _w("秒", "byou", "second", _TIME),
    _w("昼", "hiru", "daytime", _TIME),
    _w("半", "han", "half past", _TIME),
    _w("夕", "yuu", "evening", _TIME),
    _w("今", "ima", "now", _TIME),
    _w("夜", "yoru", "night", _TIME),
    _w("午", "go", "noon prefix", _TIME),
    _w("週", "shuu", "week", _TIME),
    _w("前", "mae", "before / AM", _TIME),
    _w("年", "nen", "year", _TIME),
    _w("方", "yuugata", "", _TIME),
    _w("間", "kyuukei", "jikan", _TIME),
)

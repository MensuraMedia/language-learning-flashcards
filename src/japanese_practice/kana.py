"""Kana → romaji, for the reading reference shown on a kanji card.

A kanji card is graded on its meaning, so its options are English. That leaves a
learner who cannot yet read kana fluently with readings they cannot use, which
is the opposite of a reference. Transliterating them makes the on'yomi and
kun'yomi legible from day one without changing what is scored.

**Convention.** Wapuro romaji, matching the reference charts the character data
was extracted from: long vowels are written out (シュウ → ``shuu``, チョウ →
``chou``) rather than macronned, so the text round-trips back to the same kana.
Hepburn's consonants are used throughout — ``shi``, ``chi``, ``tsu``, ``fu``,
``ji`` — never the kunrei forms. Structure is preserved: ``/`` still separates
alternative readings and okurigana stay inside their parentheses.
"""

from __future__ import annotations

__all__ = ["to_romaji"]

_DIGRAPHS: dict[str, str] = {
    "きゃ": "kya",
    "きゅ": "kyu",
    "きょ": "kyo",
    "ぎゃ": "gya",
    "ぎゅ": "gyu",
    "ぎょ": "gyo",
    "しゃ": "sha",
    "しゅ": "shu",
    "しょ": "sho",
    "じゃ": "ja",
    "じゅ": "ju",
    "じょ": "jo",
    "ちゃ": "cha",
    "ちゅ": "chu",
    "ちょ": "cho",
    "にゃ": "nya",
    "にゅ": "nyu",
    "にょ": "nyo",
    "ひゃ": "hya",
    "ひゅ": "hyu",
    "ひょ": "hyo",
    "びゃ": "bya",
    "びゅ": "byu",
    "びょ": "byo",
    "ぴゃ": "pya",
    "ぴゅ": "pyu",
    "ぴょ": "pyo",
    "みゃ": "mya",
    "みゅ": "myu",
    "みょ": "myo",
    "りゃ": "rya",
    "りゅ": "ryu",
    "りょ": "ryo",
}

_MONOGRAPHS: dict[str, str] = {
    "あ": "a",
    "い": "i",
    "う": "u",
    "え": "e",
    "お": "o",
    "か": "ka",
    "き": "ki",
    "く": "ku",
    "け": "ke",
    "こ": "ko",
    "が": "ga",
    "ぎ": "gi",
    "ぐ": "gu",
    "げ": "ge",
    "ご": "go",
    "さ": "sa",
    "し": "shi",
    "す": "su",
    "せ": "se",
    "そ": "so",
    "ざ": "za",
    "じ": "ji",
    "ず": "zu",
    "ぜ": "ze",
    "ぞ": "zo",
    "た": "ta",
    "ち": "chi",
    "つ": "tsu",
    "て": "te",
    "と": "to",
    "だ": "da",
    "ぢ": "ji",
    "づ": "zu",
    "で": "de",
    "ど": "do",
    "な": "na",
    "に": "ni",
    "ぬ": "nu",
    "ね": "ne",
    "の": "no",
    "は": "ha",
    "ひ": "hi",
    "ふ": "fu",
    "へ": "he",
    "ほ": "ho",
    "ば": "ba",
    "び": "bi",
    "ぶ": "bu",
    "べ": "be",
    "ぼ": "bo",
    "ぱ": "pa",
    "ぴ": "pi",
    "ぷ": "pu",
    "ぺ": "pe",
    "ぽ": "po",
    "ま": "ma",
    "み": "mi",
    "む": "mu",
    "め": "me",
    "も": "mo",
    "や": "ya",
    "ゆ": "yu",
    "よ": "yo",
    "ら": "ra",
    "り": "ri",
    "る": "ru",
    "れ": "re",
    "ろ": "ro",
    "わ": "wa",
    "ゐ": "i",
    "ゑ": "e",
    "を": "wo",
    "ん": "n",
    "ゃ": "ya",
    "ゅ": "yu",
    "ょ": "yo",
    "ぁ": "a",
    "ぃ": "i",
    "ぅ": "u",
    "ぇ": "e",
    "ぉ": "o",
}

#: Katakana occupy the same order as hiragana one block higher, so a single
#: offset folds one onto the other and the tables above serve both scripts.
_KATAKANA_TO_HIRAGANA = str.maketrans({chr(c): chr(c - 0x60) for c in range(0x30A1, 0x30F7)})

_VOWELS = "aiueo"


def _fold(text: str) -> str:
    return text.translate(_KATAKANA_TO_HIRAGANA)


def to_romaji(reading: str | None) -> str:
    """Transliterate a reading, leaving punctuation and unknown characters alone.

    ``None`` and the empty string map to ``""`` so callers need no guard.
    Anything that is not kana — the ``/`` between alternatives, the parentheses
    around okurigana, a stray latin letter — passes through untouched.
    """
    if not reading:
        return ""

    text = _fold(reading)
    out: list[str] = []
    i = 0
    while i < len(text):
        pair = text[i : i + 2]
        if pair in _DIGRAPHS:
            out.append(_DIGRAPHS[pair])
            i += 2
            continue

        char = text[i]
        if char == "っ":
            # A geminate doubles the consonant that follows it, so it cannot be
            # resolved without looking ahead; trailing っ has nothing to double.
            # The okurigana bracket in よっ(つ) sits between the two, so the
            # lookahead skips anything that is not itself kana.
            j = i + 1
            while j < len(text) and text[j] not in _MONOGRAPHS and text[j] != "っ":
                j += 1
            follower = _DIGRAPHS.get(text[j : j + 2]) or _MONOGRAPHS.get(text[j : j + 1], "")
            if follower and follower[0] not in _VOWELS:
                out.append("t" if follower.startswith("ch") else follower[0])
            i += 1
            continue

        if char == "ー":
            # A long mark repeats the preceding vowel.
            if out and out[-1] and out[-1][-1] in _VOWELS:
                out.append(out[-1][-1])
            i += 1
            continue

        out.append(_MONOGRAPHS.get(char, char))
        i += 1

    return "".join(out)

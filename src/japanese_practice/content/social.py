"""Phrase sets that need context to be usable.

These differ from the sets in :mod:`.phrases` in one important way: the English
gloss alone is not enough to use them safely. 強がり is not "a strong person",
it is someone putting on a brave face. さすが is praise that assumes a track
record and lands wrong without one. ばか is mild in Osaka and sharp in Tokyo.

So every card here carries a **note** — a line of context shown beneath the
meaning. A learner who sees only the gloss will use these wrongly, and using a
compliment or an insult wrongly is a more expensive mistake than mispronouncing
a kana.

Three of the sets are open stocks — praise, encouragement, description — chosen
for reach rather than pattern. Two are not:

* **Rough language** is here for *recognition*. These appear constantly in
  manga, games and television, and a learner meets them whether or not a course
  admits they exist. Every note says how hard the word lands, and the deck is
  framed as vocabulary to understand rather than to produce. 死ね in particular
  is not an insult but a thing you say to someone you want to hurt badly.
* **The 〜がり pattern** is rule-governed like 〜ましょう: an adjective stem plus
  がり names the kind of person who feels that way. 寒い → 寒がり. One rule, and
  a whole class of personality words follows.
"""

from __future__ import annotations

from ..models import CharacterSeed

__all__ = ["SOCIAL"]

_PRAISE = "Praising someone"
_ENCOURAGE = "Encouraging someone"
_DESCRIBE = "Describing things"
_ROUGH = "Rough language"
_GARI = "Personality — がり"


def _s(glyph: str, romaji: str, meaning: str, note: str, category: str) -> CharacterSeed:
    return CharacterSeed(
        glyph=glyph,
        script="phrase",
        romaji=romaji,
        meaning=meaning,
        note=note,
        category=category,
    )


_PRAISE_CARDS = (
    (
        "かっこいい",
        "kakkoii",
        "cool / sharp",
        "Of people, clothes, cars, a well-played move. Not used for cute things.",
    ),
    (
        "頭いい",
        "atama ii",
        "smart, quick-witted",
        "Casual. The full form is 頭がいい; dropping が is normal in speech.",
    ),
    (
        "よくできました",
        "yoku dekimashita",
        "well done",
        "What a teacher writes on your work. Between adults it can sound patronising.",
    ),
    (
        "すばらしい",
        "subarashii",
        "wonderful, superb",
        "Formal and safe in any company — the one to use with a boss or a stranger.",
    ),
    (
        "さすが",
        "sasuga",
        "as expected of you",
        "Praise that assumes a track record. Said to a beginner it sounds sarcastic.",
    ),
    (
        "天才",
        "tensai",
        "genius",
        "Genuine praise, but often playful — for a neat solution rather than a life's work.",
    ),
    (
        "優しいね",
        "yasashii ne",
        "you're kind",
        "About character, not politeness. A real compliment, not small talk.",
    ),
    (
        "面白いね",
        "omoshiroi ne",
        "you're funny / that's interesting",
        "面白い covers both amusing and interesting; tone and context separate them.",
    ),
    (
        "上手ですね",
        "jouzu desu ne",
        "you're good at that",
        "Said constantly to learners of Japanese. Take it as encouragement, not a verdict.",
    ),
    (
        "えらい",
        "erai",
        "well done, admirable",
        "Praises effort or doing the right thing. Common to children; warm between adults.",
    ),
)

_ENCOURAGE_CARDS = (
    (
        "がんばって",
        "ganbatte",
        "good luck / do your best",
        "The default. Said before an exam, a match, a difficult conversation.",
    ),
    (
        "頑張れ",
        "ganbare",
        "go on, you've got this",
        "The shouted form — from a crowd, or between close friends. Rough from a stranger.",
    ),
    (
        "できるよ",
        "dekiru yo",
        "you can do it",
        "Reassurance to someone doubting themselves, rather than a send-off.",
    ),
    (
        "あきらめないで",
        "akiramenaide",
        "don't give up",
        "Strong. Implies they are close to quitting, so it carries weight.",
    ),
    (
        "元気出して",
        "genki dashite",
        "cheer up",
        "For someone visibly low. Literally 'put your energy out'.",
    ),
    (
        "一緒にいるよ",
        "issho ni iru yo",
        "I'm here with you",
        "Presence rather than advice — the thing to say when there is nothing to fix.",
    ),
    (
        "もう少し",
        "mou sukoshi",
        "almost there",
        "Literally 'a little more'. Works as encouragement mid-effort.",
    ),
    (
        "応援してる",
        "ouen shiteru",
        "I'm rooting for you",
        "From 応援, the word for supporting a team. Warm and common.",
    ),
    (
        "大丈夫だよ",
        "daijoubu da yo",
        "it'll be all right",
        "Casual reassurance. The です form is politer but cooler.",
    ),
    (
        "ファイト",
        "faito",
        "you've got this",
        "From English 'fight', but means encouragement, never violence.",
    ),
)

_DESCRIBE_CARDS = (
    (
        "かわいい",
        "kawaii",
        "cute",
        "Enormously broad — people, animals, objects, handwriting. Rarely an insult.",
    ),
    (
        "きれい",
        "kirei",
        "beautiful / clean",
        "Both senses at once. A きれいな部屋 is a tidy room, not a pretty one.",
    ),
    (
        "面白い",
        "omoshiroi",
        "interesting / funny",
        "One word for both. A book, a person and a joke can all be 面白い.",
    ),
    (
        "おいしい",
        "oishii",
        "tasty",
        "Of food and drink. うまい means the same but is blunter and more masculine.",
    ),
    (
        "高い",
        "takai",
        "expensive / tall",
        "Both senses. 高いビル is a tall building; 高い店 is a pricey shop.",
    ),
    (
        "安い",
        "yasui",
        "cheap",
        "Neutral about price. To imply shoddy, Japanese uses 安っぽい instead.",
    ),
    (
        "うるさい",
        "urusai",
        "loud, noisy",
        "Also 'shut up' when barked on its own — the same word, a very different act.",
    ),
    (
        "新しい",
        "atarashii",
        "new",
        "Of objects and news alike — a new shop, or fresh information.",
    ),
)

_ROUGH_CARDS = (
    (
        "ばか",
        "baka",
        "idiot",
        "Mild in Osaka, sharper in Tokyo. Between friends it can be affectionate.",
    ),
    ("あほ", "aho", "fool", "The mirror of ばか: normal banter in Kansai, a real insult in Tokyo."),
    (
        "くそ",
        "kuso",
        "damn / crap",
        "Vulgar. Also an intensifier — くそ寒い is 'freezing', with the same register.",
    ),
    (
        "キモい",
        "kimoi",
        "gross, creepy",
        "From 気持ち悪い. Cutting when aimed at a person; common among teenagers.",
    ),
    (
        "うざい",
        "uzai",
        "annoying",
        "About a person being tiresome. Rude to their face, ordinary behind their back.",
    ),
    (
        "くさい",
        "kusai",
        "smelly",
        "Literal, and blunt. Saying it about someone is a straightforward insult.",
    ),
    (
        "頭悪い",
        "atama warui",
        "stupid",
        "The direct opposite of 頭いい, and lands hard. Not banter.",
    ),
    (
        "ブス",
        "busu",
        "ugly (of a woman)",
        "A cruel personal insult with no polite use. Know it; do not say it.",
    ),
    (
        "チビ",
        "chibi",
        "shorty",
        "Mocks height. Affectionate for pets and small children, hurtful to adults.",
    ),
    (
        "死ね",
        "shine",
        "drop dead",
        "The most serious item here. Not banter in any register — it is said to wound.",
    ),
)

_GARI_CARDS = (
    (
        "寒がり",
        "samugari",
        "someone who feels the cold",
        "寒い + がり. Not 'cold person' — it describes sensitivity, not temperature.",
    ),
    (
        "暑がり",
        "atsugari",
        "someone who feels the heat",
        "The pair to 寒がり. Both describe a constitution, not a mood.",
    ),
    (
        "怖がり",
        "kowagari",
        "someone easily frightened",
        "From 怖い. Gentle rather than mocking — often said of oneself.",
    ),
    (
        "恥ずかしがり",
        "hazukashigari",
        "a shy person",
        "From 恥ずかしい. Often 恥ずかしがり屋, with 屋 marking it as a trait.",
    ),
    (
        "面倒くさがり",
        "mendokusagari",
        "someone who can't be bothered",
        "From 面倒くさい. Self-deprecating when said about oneself.",
    ),
    (
        "強がり",
        "tsuyogari",
        "someone putting on a brave face",
        "From 強い — but it means bluffing, not strength. The gloss alone misleads.",
    ),
    (
        "寂しがり",
        "sabishigari",
        "someone who gets lonely easily",
        "From 寂しい. Affectionate; often 寂しがり屋.",
    ),
)

#: 55 cards across five sets.
SOCIAL: tuple[CharacterSeed, ...] = (
    *(_s(g, r, m, n, _PRAISE) for g, r, m, n in _PRAISE_CARDS),
    *(_s(g, r, m, n, _ENCOURAGE) for g, r, m, n in _ENCOURAGE_CARDS),
    *(_s(g, r, m, n, _DESCRIBE) for g, r, m, n in _DESCRIBE_CARDS),
    *(_s(g, r, m, n, _ROUGH) for g, r, m, n in _ROUGH_CARDS),
    *(_s(g, r, m, n, _GARI) for g, r, m, n in _GARI_CARDS),
)

"""Phrase sets built on a shared pattern.

Every set here is chosen because **one structure generates all of it**. Learn
that 〜ましょう turns a verb into "let's", and 行きましょう, 食べましょう and
飲みましょう all arrive together. That is a different kind of learning from
memorising ten unrelated sentences, and it is what makes these worth cards.

The sets are also chosen for reach: a learner who can ask for a bag, say how
they are paying and ask the price can complete a real transaction, which no
amount of isolated vocabulary achieves.

**On accuracy.** These are authored, not extracted — the reference worksheets
cover vocabulary rather than conversation. That is defensible *only* because
each set is either rule-governed (the 〜ましょう and 〜てください patterns are
mechanical) or a small stock of set phrases that every beginner course teaches
identically. Open-ended phrase vocabulary is deliberately still absent: writing
it from memory would produce confident, plausible, unverifiable content, which
is the worst possible thing to put in a learning tool.

Politeness is kept consistent inside each set. Mixing 行こう with 食べましょう
would teach the register as noise rather than as a choice, so the volitional set
is uniformly polite; the casual forms belong to their own future set.
"""

from __future__ import annotations

from ..models import CharacterSeed

__all__ = ["PHRASES"]

_LIKES = "Saying you like it"
_KONBINI = "At the convenience store"
_LETS = "Let's — ましょう"
_REQUESTS = "Please — てください"
_BASICS = "Getting by"


def _p(glyph: str, romaji: str, meaning: str, category: str) -> CharacterSeed:
    """A phrase card.

    ``script="phrase"`` rather than ``"vocab"``: a phrase is a different object
    from a word, needs more room on screen, and belongs on its own shelf.
    """
    return CharacterSeed(
        glyph=glyph,
        script="phrase",
        romaji=romaji,
        meaning=meaning,
        category=category,
    )


#: Reacting well is most of early conversation. These are the words that carry
#: enthusiasm, and they are adjectives and nouns rather than sentences, so they
#: work on their own without any grammar attached.
_LIKE_PHRASES = (
    ("大好き", "daisuki", "I love it"),
    ("好き", "suki", "I like it"),
    ("おいしい", "oishii", "it's delicious"),
    ("かわいい", "kawaii", "it's cute"),
    ("すごい", "sugoi", "amazing / wow"),
    ("最高", "saikou", "the best"),
    ("楽しみ", "tanoshimi", "I'm looking forward to it"),
    ("気に入った", "ki ni itta", "I've taken a liking to it"),
    ("ファンです", "fan desu", "I'm a fan"),
    ("いいね", "ii ne", "nice / I like that"),
)

#: A complete convenience-store transaction. Ordered as it actually happens:
#: you hand over the item, they ask about heating and a bag, you pay, you take
#: the receipt.
_KONBINI_PHRASES = (
    ("これください", "kore kudasai", "this one, please"),
    ("いくらですか", "ikura desu ka", "how much is it?"),
    ("温めてください", "atatamete kudasai", "please heat it up"),
    ("袋をください", "fukuro o kudasai", "a bag, please"),
    ("袋はいりません", "fukuro wa irimasen", "no bag, thank you"),
    ("お箸をください", "ohashi o kudasai", "chopsticks, please"),
    ("カードで", "kaado de", "by card"),
    ("現金で", "genkin de", "with cash"),
    ("レシートをください", "reshiito o kudasai", "a receipt, please"),
    ("大丈夫です", "daijoubu desu", "I'm fine, thanks / no need"),
)

#: The 〜ましょう pattern. Take the polite stem and add ましょう: 行きます →
#: 行きましょう. One rule, and every verb you know becomes an invitation.
_LETS_PHRASES = (
    ("行きましょう", "ikimashou", "let's go"),
    ("食べましょう", "tabemashou", "let's eat"),
    ("飲みましょう", "nomimashou", "let's drink"),
    ("しましょう", "shimashou", "let's do it"),
    ("見ましょう", "mimashou", "let's watch / let's look"),
    ("始めましょう", "hajimemashou", "let's begin"),
    ("帰りましょう", "kaerimashou", "let's head home"),
    ("待ちましょう", "machimashou", "let's wait"),
    ("休みましょう", "yasumimashou", "let's take a break"),
    ("話しましょう", "hanashimashou", "let's talk"),
)

#: The 〜てください pattern. Take the te-form and add ください: 待って →
#: 待ってください. The same rule turns any verb into a polite request.
_REQUEST_PHRASES = (
    ("待ってください", "matte kudasai", "please wait"),
    ("見せてください", "misete kudasai", "please show me"),
    ("教えてください", "oshiete kudasai", "please tell me"),
    ("書いてください", "kaite kudasai", "please write it down"),
    ("来てください", "kite kudasai", "please come"),
    ("手伝ってください", "tetsudatte kudasai", "please help me"),
    ("ゆっくり話してください", "yukkuri hanashite kudasai", "please speak slowly"),
    ("もう一度お願いします", "mou ichido onegaishimasu", "once more, please"),
)

#: The phrases that get you out of trouble. Not a pattern — a stock — but the
#: highest-reach set in the file: these work in any situation at all.
_BASIC_PHRASES = (
    ("すみません", "sumimasen", "excuse me / sorry"),
    ("ありがとうございます", "arigatou gozaimasu", "thank you"),
    ("お願いします", "onegaishimasu", "please / if you would"),
    ("わかりません", "wakarimasen", "I don't understand"),
    ("わかりました", "wakarimashita", "understood"),
    ("英語でいいですか", "eigo de ii desu ka", "is English all right?"),
    ("日本語が少しわかります", "nihongo ga sukoshi wakarimasu", "I understand a little Japanese"),
    ("どこですか", "doko desu ka", "where is it?"),
    ("何ですか", "nan desu ka", "what is it?"),
    ("失礼します", "shitsurei shimasu", "excuse me (entering or leaving)"),
)

#: 48 phrases across five sets.
PHRASES: tuple[CharacterSeed, ...] = (
    *(_p(g, r, m, _LIKES) for g, r, m in _LIKE_PHRASES),
    *(_p(g, r, m, _KONBINI) for g, r, m in _KONBINI_PHRASES),
    *(_p(g, r, m, _LETS) for g, r, m in _LETS_PHRASES),
    *(_p(g, r, m, _REQUESTS) for g, r, m in _REQUEST_PHRASES),
    *(_p(g, r, m, _BASICS) for g, r, m in _BASIC_PHRASES),
)

"""General words: the everyday vocabulary a textbook teaches as one word.

English gives a learner *one* word where Japanese gives a dozen, each carrying a
different degree of confidence, formality or disbelief. "Maybe" is たぶん at 80%
certainty and かもしれない at 40%; both translate to "maybe", and choosing wrongly
either overstates a guess or undersells a near-certainty. That distinction is
invisible in a gloss, so every card here carries **an example sentence** showing
the word doing its job in context.

Eight sets. Seven are near-synonym sets and behave differently from everything
else in the app:

* **Maybe**, **Not bad**, **Seriously**, **Sorry**, **Thanks**, **Very** and
  **Saying no** are *near-synonym* sets. Multiple
  choice cannot test them, because every option means roughly the same thing —
  a learner picking "probably" from a list of four words that all mean
  "probably" learns nothing, and the exercise grades their ability to spot
  which gloss was typed rather than whether they know the word. These open in
  **review** mode: read, flip, and grade yourself honestly. See
  :data:`japanese_practice.session.CHALLENGES`.
* **Question words** are genuinely distinct — what, where, why, when — so they
  take multiple choice like any other deck.

**On accuracy.** These are authored rather than extracted, which is defensible
only because every entry is high-frequency spoken Japanese that any beginner
course teaches identically, and because each is pinned to a concrete sentence
rather than left as a bare gloss. Register is stated in the note wherever it
matters: マジで is fine among friends and wrong in a meeting, and a learner who
takes it as a neutral synonym for 本当に will use it badly.
"""

from __future__ import annotations

from ..models import CharacterSeed

__all__ = ["GENERAL"]

_MAYBE = "Maybe — degrees of certainty"
_NOTBAD = "Not bad — faint praise"
_SERIOUSLY = "Seriously — surprise and disbelief"
_QUESTION = "Question words"


def _g(glyph: str, romaji: str, meaning: str, note: str, category: str) -> CharacterSeed:
    """A general-word card.

    ``script="phrase"`` rather than a new script of its own: these are short
    expressions, they are graded on meaning, they need the wide card and they
    carry a note — every one of which the phrase machinery already does. The
    shelf is decided by ``DECK_META``, not by the script, so a separate shelf
    costs nothing here.
    """
    return CharacterSeed(
        glyph=glyph,
        script="phrase",
        romaji=romaji,
        meaning=meaning,
        note=note,
        category=category,
    )


#: Ordered by **confidence**, from near-certain down to openly evasive. That
#: ordering is the lesson: these are not interchangeable, they are a scale, and
#: seeing them in sequence is what makes the difference legible.
_MAYBE_CARDS = (
    (
        "たぶん",
        "tabun",
        "probably",
        "The confident one — around 80% sure. 「たぶん行きます」 I'll probably go.",
    ),
    (
        "おそらく",
        "osoraku",
        "in all likelihood",
        "Same confidence as たぶん but formal — writing and speeches. "
        "「おそらく雨になるでしょう」 It will in all likelihood rain.",
    ),
    (
        "でしょう",
        "deshou",
        "probably (sentence-final)",
        "Attaches to a statement rather than standing alone. "
        "「明日は寒いでしょう」 It'll probably be cold tomorrow.",
    ),
    (
        "かもしれない",
        "kamo shirenai",
        "might, may",
        "A genuine coin-toss, far less sure than たぶん. "
        "「雨が降るかもしれない」 It might rain.",
    ),
    (
        "かも",
        "kamo",
        "might (casual)",
        "The clipped form of かもしれない, and very common in speech. " "「行くかも」 I might go.",
    ),
    (
        "もしかしたら",
        "moshikashitara",
        "possibly, just maybe",
        "Opens the sentence and flags an outside chance; usually paired with "
        "かも. 「もしかしたら休みかも」 It might just be closed.",
    ),
    (
        "ひょっとしたら",
        "hyotto shitara",
        "on the off chance",
        "As もしかしたら but rarer and a shade more surprised. "
        "「ひょっとしたら知り合いかも」 They might just be an acquaintance.",
    ),
    (
        "気がする",
        "ki ga suru",
        "I get the feeling",
        "A hunch rather than evidence. 「合ってる気がする」 I get the feeling " "that's right.",
    ),
    (
        "どうかな",
        "dou kana",
        "I wonder / not sure",
        "Voices doubt about someone else's claim. 「間に合うかな」 I wonder if " "we'll make it.",
    ),
    (
        "さあ",
        "saa",
        "who knows",
        "Declines to guess at all — an answer in itself, not rudeness. "
        "「さあ、分かりません」 Search me, I don't know.",
    ),
)

#: Faint praise, ordered from warmest to most grudging. Japanese is rich here
#: because direct praise can sound overbearing, so "not bad" does a great deal
#: of the work that "great" does in English.
_NOTBAD_CARDS = (
    (
        "悪くない",
        "warukunai",
        "not bad",
        "Literally 'not bad', and like the English it is quiet approval. "
        "「この店、悪くないね」 This place isn't bad, is it.",
    ),
    (
        "なかなか",
        "nakanaka",
        "quite good, better than expected",
        "Carries surprise — it was better than you assumed. "
        "「なかなかおいしい」 That's really quite tasty.",
    ),
    (
        "けっこういい",
        "kekkou ii",
        "pretty good",
        "Warmer than 悪くない and unambiguously positive. "
        "「けっこういい映画だった」 It was a pretty good film.",
    ),
    (
        "思ったよりいい",
        "omotta yori ii",
        "better than I expected",
        "States the comparison outright. 「思ったよりいいね」 That's better " "than I expected.",
    ),
    (
        "上出来",
        "joudeki",
        "a good job, well done",
        "Praises a *result*, often one that beat expectations. "
        "「初めてなら上出来だよ」 For a first attempt that's a good job.",
    ),
    (
        "いける",
        "ikeru",
        "pretty decent, works for me",
        "Casual, and used most about food and drink. " "「これ、いけるね」 This is pretty decent.",
    ),
    (
        "まあまあ",
        "maamaa",
        "so-so, alright",
        "The honest middle — neither good nor bad. " "「味はまあまあ」 The taste is just alright.",
    ),
    (
        "そこそこ",
        "sokosoko",
        "decent enough, adequate",
        "Sufficient but not more; slightly cooler than まあまあ. "
        "「そこそこ売れている」 It sells well enough.",
    ),
    (
        "まし",
        "mashi",
        "better than the alternative",
        "Praise only by comparison — the least bad option. "
        "「歩くよりましだ」 It's better than walking.",
    ),
    (
        "そんなに悪くない",
        "sonna ni warukunai",
        "not *that* bad",
        "Defends something against a low opinion already voiced. "
        "「そんなに悪くないと思う」 I don't think it's that bad.",
    ),
)

#: Disbelief and emphasis, ordered from neutral to slang. **Register is the
#: whole lesson here** — these are not interchangeable, and the wrong one in a
#: meeting is a real mistake, so every note states where the word belongs.
_SERIOUSLY_CARDS = (
    (
        "本当に",
        "hontou ni",
        "really, truly",
        "The neutral one — safe in any company. " "「本当にありがとう」 Thank you, really.",
    ),
    (
        "本当？",
        "hontou?",
        "really?",
        "A plain request to confirm, with no disbelief implied. "
        "「本当？知らなかった」 Really? I had no idea.",
    ),
    (
        "ほんと？",
        "honto?",
        "really? (casual)",
        "The clipped everyday form of 本当？. " "「ほんと？やった！」 Really? Brilliant!",
    ),
    (
        "マジで",
        "majide",
        "seriously, for real",
        "Slang. Fine among friends, wrong at work or with strangers. "
        "「マジで疲れた」 I'm seriously tired.",
    ),
    (
        "マジ？",
        "maji?",
        "seriously?",
        "The question form, and very common in casual speech. " "「マジ？いつ？」 Seriously? When?",
    ),
    (
        "ガチで",
        "gachi de",
        "for real, no exaggeration",
        "Stronger and newer than マジで; from sumo's 'ガチンコ', a real bout. "
        "「ガチで無理」 That's genuinely impossible.",
    ),
    (
        "本気？",
        "honki?",
        "are you serious?",
        "Asks about *intent*, not fact — do you actually mean to do that. "
        "「本気？やめときなよ」 You're serious? I'd leave it.",
    ),
    (
        "嘘でしょ",
        "uso desho",
        "you're kidding",
        "Literally 'that's a lie, right' — dismay, not an accusation. "
        "「嘘でしょ、また？」 You're kidding, again?",
    ),
    (
        "嘘！",
        "uso!",
        "no way!",
        "Blurted on hearing surprising news. Nobody is calling anybody a liar. "
        "「嘘！すごい！」 No way! That's amazing!",
    ),
    (
        "まさか",
        "masaka",
        "surely not, you don't say",
        "Disbelief at something you had thought impossible. "
        "「まさか、彼が？」 Surely not — him?",
    ),
    (
        "信じられない",
        "shinjirarenai",
        "I can't believe it",
        "Works for delight and for outrage alike. "
        "「信じられない、勝った！」 I can't believe it, we won!",
    ),
)

#: The interrogatives. Genuinely distinct meanings, so this set takes multiple
#: choice. Each note gives the word in a full question, because the particle it
#: takes is half of knowing it.
_QUESTION_CARDS = (
    (
        "何",
        "nani / nan",
        "what",
        "なに alone; なん before です and counters. " "「これは何ですか」 What is this?",
    ),
    (
        "どこ",
        "doko",
        "where",
        "「トイレはどこですか」 Where is the toilet?",
    ),
    (
        "誰",
        "dare",
        "who",
        "「あの人は誰ですか」 Who is that person?",
    ),
    (
        "いつ",
        "itsu",
        "when",
        "Takes no particle before です. 「いつ行きますか」 When are you going?",
    ),
    (
        "どうして",
        "doushite",
        "why (everyday)",
        "The everyday 'why', neutral in tone. " "「どうして遅れたの」 Why were you late?",
    ),
    (
        "なんで",
        "nande",
        "why (casual)",
        "Same meaning as どうして but blunter; can sound accusing. "
        "「なんで言わなかったの」 Why didn't you say so?",
    ),
    (
        "なぜ",
        "naze",
        "why (formal)",
        "Writing, news and formal speech rather than conversation. "
        "「なぜ起きたのか」 Why did it happen?",
    ),
    (
        "どう",
        "dou",
        "how, in what way",
        "Asks after manner or opinion. 「どう思いますか」 What do you think?",
    ),
    (
        "どうやって",
        "douyatte",
        "how, by what means",
        "Asks for the method specifically. " "「どうやって行きますか」 How do you get there?",
    ),
    (
        "どれ",
        "dore",
        "which one (of three or more)",
        "Stands alone. 「どれがいいですか」 Which one would you like?",
    ),
    (
        "どっち",
        "docchi",
        "which (of two)",
        "Two options only; the formal form is どちら. "
        "「コーヒーとお茶、どっち？」 Coffee or tea, which?",
    ),
    (
        "どの",
        "dono",
        "which (before a noun)",
        "Always attaches to a noun, unlike どれ. " "「どの電車ですか」 Which train is it?",
    ),
    (
        "いくら",
        "ikura",
        "how much (price)",
        "「これはいくらですか」 How much is this?",
    ),
    (
        "いくつ",
        "ikutsu",
        "how many, how old",
        "General counting, and a child's age. " "「いくつありますか」 How many are there?",
    ),
)


# ── Register scales ─────────────────────────────────────────────────────────
# The four sets below all teach the same kind of thing: **how formal, how
# strong, how blunt**. Every member is a correct translation of the English
# headword, so the only question a card can usefully ask is *which one belongs
# here* — which is why they are review sets like the three above.
#
# A few obvious members are missing because they are already seeded elsewhere,
# and a glyph is unique per script: すみません and ありがとうございます live in
# Getting by, 大丈夫です in At the convenience store, なかなか in Not bad. Each
# note names the absent relative rather than pretending it does not exist.

_SORRY = "Sorry — degrees of contrition"
_THANKS = "Thanks — degrees of gratitude"
_VERY = "Very — degrees of intensity"
_NO = "Saying no without saying no"

#: Casual to formal. Getting this wrong is the expensive mistake in this file:
#: ごめん to a manager is not a small error, and no gloss of "sorry" shows it.
_SORRY_CARDS = (
    (
        "悪い",
        "warui",
        "my bad",
        "The most casual, and mostly male. Only for friends. " "「悪い、遅れた」 My bad, I'm late.",
    ),
    (
        "ごめん",
        "gomen",
        "sorry",
        "Friends and family. Warm, but far too light for a stranger or a "
        "manager. 「ごめん、忘れてた」 Sorry, I forgot.",
    ),
    (
        "ごめんなさい",
        "gomen nasai",
        "I'm sorry",
        "The full form — more sincere than ごめん and usable with people you "
        "know. 「ごめんなさい、私のミスです」 I'm sorry, it was my mistake.",
    ),
    (
        "すいません",
        "suimasen",
        "sorry / excuse me (spoken)",
        "The everyday spoken form of すみません, which is the written standard "
        "and appears in Getting by. 「すいません、これお願いします」 Excuse me, "
        "this please.",
    ),
    (
        "どうもすみません",
        "doumo sumimasen",
        "I'm really sorry",
        "どうも intensifies it. Still polite rather than formal. "
        "「どうもすみません、お待たせしました」 I'm so sorry to have kept you.",
    ),
    (
        "失礼しました",
        "shitsurei shimashita",
        "my apologies",
        "For a lapse in *manners* — an interruption, a wrong number. Also said "
        "on leaving a room. 「失礼しました、間違えました」 My apologies, I had it "
        "wrong.",
    ),
    (
        "申し訳ありません",
        "moushiwake arimasen",
        "I'm terribly sorry",
        "The business standard, and a real step up. Literally 'there is no "
        "excuse'. 「ご迷惑をおかけして申し訳ありません」 I'm terribly sorry for "
        "the trouble.",
    ),
    (
        "申し訳ございません",
        "moushiwake gozaimasen",
        "I am profoundly sorry",
        "The most formal in ordinary use — staff to customers. Anything heavier "
        "belongs to a press conference. 「申し訳ございません、ただいま確認します」",
    ),
    (
        "お待たせしました",
        "omatase shimashita",
        "sorry to have kept you waiting",
        "Said on arriving late *and* routinely when serving — an apology by "
        "form rather than by fault. 「お待たせしました、こちらへどうぞ」",
    ),
    (
        "反省しています",
        "hansei shite imasu",
        "I regret it",
        "Accepts fault rather than expressing sympathy. Weighty — it says you "
        "have thought about what you did. 「反省しています。二度としません」",
    ),
)

#: Casual to formal, plus the one that catches everybody: thanking someone by
#: apologising to them.
_THANKS_CARDS = (
    (
        "サンキュー",
        "sankyuu",
        "thanks",
        "From English, and very casual — friends only. "
        "「サンキュー、助かる」 Thanks, that helps.",
    ),
    (
        "どうも",
        "doumo",
        "thanks (clipped)",
        "Light and slightly brusque on its own. Does duty as a greeting too. "
        "「どうも、また明日」 Thanks, see you tomorrow.",
    ),
    (
        "ありがとう",
        "arigatou",
        "thank you",
        "The neutral casual form. Add ございます for anyone senior — that form "
        "is seeded in Getting by. Note that Japanese also thanks by "
        "*apologising*: すみません means thank you when the favour cost the "
        "other person something. 「本当にありがとう」 Thank you, really.",
    ),
    (
        "どうもありがとうございます",
        "doumo arigatou gozaimasu",
        "thank you very much",
        "どうも intensifies the polite form. Safe anywhere. "
        "「どうもありがとうございます、助かりました」",
    ),
    (
        "ありがとうございました",
        "arigatou gozaimashita",
        "thank you (for what is now done)",
        "**Past tense, and it matters**: ございます thanks for something "
        "ongoing, ございました for something finished. Said on leaving a shop.",
    ),
    (
        "助かりました",
        "tasukarimashita",
        "you saved me",
        "Thanks *for the effect* — it acknowledges you were in trouble. Warmer "
        "than a bare thank you. 「助かりました、ありがとう」",
    ),
    (
        "恐れ入ります",
        "osoreirimasu",
        "much obliged",
        "Formal business thanks, with a note of deference. Also softens a "
        "request. 「恐れ入りますが、少々お待ちください」",
    ),
    (
        "感謝しています",
        "kansha shite imasu",
        "I'm grateful",
        "Heartfelt and weighty — for something that mattered, not for a held "
        "door. 「いつも感謝しています」 I'm always grateful.",
    ),
    (
        "お世話になりました",
        "osewa ni narimashita",
        "thank you for everything",
        "Thanks for a period of care — leaving a job, a school, a host family. "
        "No English single-word equivalent. 「大変お世話になりました」",
    ),
    (
        "ごちそうさまでした",
        "gochisousama deshita",
        "thank you for the meal",
        "Said after eating, always — at home, in a restaurant, to whoever paid. "
        "Omitting it is noticeable. 「ごちそうさまでした、おいしかったです」",
    ),
)

#: A ladder, weakest to strongest, with the register noted at each rung.
_VERY_CARDS = (
    (
        "ちょっと",
        "chotto",
        "a little",
        "The bottom of the ladder. Also the standard softener — and, left "
        "unfinished, a refusal. 「ちょっと高い」 It's a bit expensive.",
    ),
    (
        "わりと",
        "warito",
        "fairly, relatively",
        "Mild, and carries mild surprise. 「わりと簡単だった」 It was fairly " "easy, actually.",
    ),
    (
        "けっこう",
        "kekkou",
        "quite, rather",
        "More than expected. Note けっこうです is a *refusal* — same word, "
        "different job. 「けっこう歩いたね」 We walked quite a way.",
    ),
    (
        "かなり",
        "kanari",
        "considerably",
        "Objectively a lot; neutral in register. "
        "「かなり時間がかかる」 It takes considerably longer.",
    ),
    (
        "とても",
        "totemo",
        "very",
        "The safe default — polite, neutral, never wrong. "
        "「とても面白かったです」 It was very interesting.",
    ),
    (
        "すごく",
        "sugoku",
        "really",
        "Slightly more casual than とても and far more common in speech. "
        "「すごく嬉しい」 I'm really happy.",
    ),
    (
        "めっちゃ",
        "meccha",
        "super, dead",
        "Kansai in origin, now general slang. Friends only. "
        "「めっちゃおいしい」 This is super tasty.",
    ),
    (
        "超",
        "chou",
        "ultra, mega",
        "Youth slang, attached directly to the word. Wrong in any formal "
        "setting. 「超楽しかった」 It was mega fun.",
    ),
    (
        "非常に",
        "hijou ni",
        "extremely (formal)",
        "Writing, reports and speeches — stilted in conversation. "
        "「非常に重要な問題です」 It is an extremely important matter.",
    ),
    (
        "全然",
        "zenzen",
        "not at all — or totally",
        "**Two opposite jobs.** With a negative it means 'not at all'; in "
        "casual speech it also means 'totally'. 「全然分からない」 I don't "
        "understand at all. 「全然大丈夫」 Totally fine.",
    ),
)

#: Japanese rarely refuses outright, so the refusal is carried by form. A
#: learner who only knows いいえ will both miss refusals aimed at them and
#: sound harsh giving their own.
_NO_CARDS = (
    (
        "ちょっと…",
        "chotto...",
        "that's a bit…",
        "**The sentence is left unfinished on purpose** — trailing off is the "
        "refusal. The same ちょっと as 'a little'. 「明日はちょっと…」 Tomorrow "
        "is a bit… (= no).",
    ),
    (
        "結構です",
        "kekkou desu",
        "no thank you",
        "**A trap: it can also mean 'that's fine'.** Tone and context decide. "
        "Offered a bag, it declines. 「袋は結構です」 No bag, thanks.",
    ),
    (
        "いいです",
        "ii desu",
        "I'm good (declining)",
        "The same ambiguity — literally 'it's good', usually meaning 'no "
        "need'. 「いいです、自分でやります」 It's fine, I'll do it myself.",
    ),
    (
        "遠慮しておきます",
        "enryo shite okimasu",
        "I'll pass",
        "A polite, unmistakable decline. 遠慮 is holding back out of "
        "consideration. 「今回は遠慮しておきます」 I'll pass this time.",
    ),
    (
        "難しいです",
        "muzukashii desu",
        "that would be difficult (= no)",
        "Almost never about difficulty. Business Japanese for no. "
        "「その日程は難しいです」 That schedule would be difficult.",
    ),
    (
        "考えておきます",
        "kangaete okimasu",
        "I'll think about it",
        "Usually a soft no, not a maybe. Read it as a closed door unless they "
        "follow up. 「考えておきます」 I'll give it some thought.",
    ),
    (
        "また今度",
        "mata kondo",
        "some other time",
        "Declines an invitation while keeping the relationship. Rarely names a "
        "date. 「また今度にしましょう」 Let's make it another time.",
    ),
    (
        "やめておきます",
        "yamete okimasu",
        "I'll give it a miss",
        "Declines a choice you were offered — a dish, a plan. "
        "「今日はやめておきます」 I'll give it a miss today.",
    ),
    (
        "できません",
        "dekimasen",
        "I can't",
        "Direct and neutral — states inability rather than unwillingness. "
        "「それはできません」 I can't do that.",
    ),
    (
        "無理",
        "muri",
        "no way, not happening",
        "Blunt and casual. Fine with friends, harsh upward. "
        "「明日までは無理」 By tomorrow is not happening.",
    ),
)


#: 85 cards across eight sets.
GENERAL: tuple[CharacterSeed, ...] = (
    *(_g(g, r, m, n, _MAYBE) for g, r, m, n in _MAYBE_CARDS),
    *(_g(g, r, m, n, _NOTBAD) for g, r, m, n in _NOTBAD_CARDS),
    *(_g(g, r, m, n, _SERIOUSLY) for g, r, m, n in _SERIOUSLY_CARDS),
    *(_g(g, r, m, n, _QUESTION) for g, r, m, n in _QUESTION_CARDS),
    *(_g(g, r, m, n, _SORRY) for g, r, m, n in _SORRY_CARDS),
    *(_g(g, r, m, n, _THANKS) for g, r, m, n in _THANKS_CARDS),
    *(_g(g, r, m, n, _VERY) for g, r, m, n in _VERY_CARDS),
    *(_g(g, r, m, n, _NO) for g, r, m, n in _NO_CARDS),
)

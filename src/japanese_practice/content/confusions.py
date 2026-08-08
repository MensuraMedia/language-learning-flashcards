"""Visually confusable kana pairs.

Each tuple is a pair of glyphs that learners genuinely mix up on sight —
mirrored shapes (き/さ), stroke-direction pairs (シ/ツ, ソ/ン) and
near-identical skeletons (は/ほ, ル/レ). Pairs are unordered: a pair is
listed once, and ``(a, b)`` implies ``(b, a)``.

Only shape confusions are listed. Homophone traps such as じ/ぢ or ず/づ are
reading collisions rather than visual ones and are deliberately excluded.

The list spans all three scripts. Callers that want one script's pairs filter
by the script of the glyphs, which the ``characters`` table already records —
the pairs themselves carry no script tag, because a pair is a fact about two
shapes rather than about a curriculum.
"""

CONFUSION_PAIRS: list[tuple[str, str]] = [
    # --- hiragana ---
    ("あ", "お"),
    ("あ", "め"),
    ("ぬ", "め"),
    ("ぬ", "の"),
    ("ぬ", "る"),
    ("る", "ろ"),
    ("れ", "わ"),
    ("れ", "ね"),
    ("わ", "ね"),
    ("は", "ほ"),
    ("は", "け"),
    ("ほ", "ま"),
    ("ま", "も"),
    ("き", "さ"),
    ("さ", "ち"),
    ("ち", "ら"),
    ("い", "り"),
    ("た", "な"),
    ("す", "む"),
    ("し", "つ"),
    ("こ", "に"),
    # --- katakana ---
    ("シ", "ツ"),
    ("シ", "ン"),
    ("ソ", "ン"),
    ("ソ", "ツ"),
    ("ソ", "ノ"),
    ("ン", "ノ"),
    ("ク", "ワ"),
    ("ク", "タ"),
    ("ク", "ケ"),
    ("ワ", "ウ"),
    ("ワ", "ヲ"),
    ("ウ", "フ"),
    ("ヲ", "ラ"),
    ("コ", "ユ"),
    ("コ", "ヨ"),
    ("テ", "チ"),
    ("マ", "ム"),
    ("マ", "ア"),
    ("ア", "ヤ"),
    ("ス", "ヌ"),
    ("ヌ", "メ"),
    ("ル", "レ"),
    ("オ", "ホ"),
    ("ナ", "メ"),
    # --- kanji: near-identical skeletons, one stroke or one dot apart ---
    ("人", "入"),
    ("大", "犬"),
    ("大", "太"),
    ("日", "白"),
    ("日", "目"),
    ("千", "干"),
    ("石", "右"),
    ("貝", "見"),
    ("午", "牛"),
    ("木", "本"),
    ("木", "休"),
    ("手", "毛"),
    ("田", "由"),
    ("田", "申"),
    ("天", "夫"),
    ("白", "百"),
    ("万", "方"),
    ("名", "各"),
    ("会", "合"),
    ("待", "持"),
    ("問", "間"),
    ("料", "科"),
    ("借", "貸"),
    ("使", "便"),
    ("客", "各"),
    ("土", "工"),
    ("牛", "生"),
    ("犬", "太"),
    ("押", "抽"),
    ("開", "閉"),
    ("問", "門"),
    ("鳥", "島"),
    ("線", "緑"),
    ("績", "積"),
    ("績", "責"),
    ("複", "復"),
    ("像", "象"),
    ("経", "軽"),
    ("課", "果"),
]

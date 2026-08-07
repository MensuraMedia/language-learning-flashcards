"""Visually confusable kana pairs.

Each tuple is a pair of glyphs that learners genuinely mix up on sight —
mirrored shapes (き/さ), stroke-direction pairs (シ/ツ, ソ/ン) and
near-identical skeletons (は/ほ, ル/レ). Pairs are unordered: a pair is
listed once, and ``(a, b)`` implies ``(b, a)``.

Only shape confusions are listed. Homophone traps such as じ/ぢ or ず/づ are
reading collisions rather than visual ones and are deliberately excluded.
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
]

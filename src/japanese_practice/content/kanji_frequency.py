"""Kanji ordered by teaching frequency.

Taken from the Mensura Media ``flashcard_kanji_500.pdf`` deck in the companion
`language-learning <https://github.com/MensuraMedia/language-learning>`_
repository — the same order its printed Top 200 and Top 500 card sets use, so
the on-screen volume tiers and the printed decks agree. The Top 200 set is
exactly the first 200 entries here, which was verified against
``flashcard_kanji_200.pdf``.

This is a *teaching* order rather than a corpus frequency count: it front-loads
numbers, days and the kanji a beginner meets first. It is deliberately separate
from the JLPT levels — a learner working by volume crosses several levels at
once, which is the point of the tier.
"""

from __future__ import annotations

__all__ = ["KANJI_BY_FREQUENCY"]

#: 500 glyphs, most-taught first. Index + 1 is the rank stored on each row.
KANJI_BY_FREQUENCY: tuple[str, ...] = tuple(
    "".join(
        "一二三四五六七八九十百千万円日月火水木金土曜年時分半毎今先後前午間週人子女男友父母大小中長高安新古白"
        "多少上下右左北南東西口目耳手足山川天気雨花田本校学生語国外名何電車道駅店会社食飲見聞読書話言行来出入"
        "休立買空青赤夕兄姉弟妹家族親主夫妻彼自体頭顔声心力病医薬死海池地野林森石風雪光春夏秋冬朝昼夜暗明黒黄"
        "室屋堂館院場市町村区京都県世界門広走歩止送届通運乗動引押開閉始終集持待座使作売借貸返払切洗消着知思考"
        "教習研究問答意味歌映画写真特別同太細強弱重軽近遠早遅速悪正不便利急忙楽若有無飯茶料理工業産品物服紙字"
        "文質題試験度回番号色音鳥魚犬牛馬肉英漢計記説転以全部員注発去変与争交介仏代件任伝位住例供価保信倒値側"
        "備債兵具典内制刺則割加助努労効務勤勧化協印危厚原参及反収取受台史合向否含告命商喜器因団囲圧在型域報境"
        "壁央失奥存季守完官定実客宿富寒寝寺対導居属島布師席帰常幅干平床底庭建式張当形影役律従得必忍志応念怒性"
        "恋恐息患悲情想感態成戦戻打技投抗抜抵抽担拾指挙捕探接掲換損撮支攻政救敗散数整断方星望期札束条松板果柱"
        "査株根格械権橋機次欺武歴残比毛民氷求汚決治況法泡波泣活派流浅涼深混清済渡温港湖湿準煙照熱犯状猫獲率現"
    )
)

assert len(KANJI_BY_FREQUENCY) == 500, "the volume tiers slice this list directly"

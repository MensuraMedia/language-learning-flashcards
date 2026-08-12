"""The formatting contract from docs/UI-FORMAT.md, where it can be asserted.

These guard the two rules that have actually been broken in this project:
headings styled by specificity rather than named by role, and an accent written
as a literal so it cannot follow the theme.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent / "src/japanese_practice"
CSS = (ROOT / "static/css/theme.css").read_text()
TEMPLATES = sorted((ROOT / "templates").glob("*.html"))
SCRIPTS = sorted((ROOT / "static/js").glob("*.js"))

#: Every accent must resolve through this variable. `.theme-kanji` overrides it,
#: so anything using a literal stays amber on a green screen.
ACCENT_LITERALS = re.compile(r"#f0b429|#4ade80", re.I)


def test_the_accent_is_only_ever_a_variable():
    """A literal accent cannot follow `.theme-kanji`.

    The theme works by overriding `--amber`; a component that hard-codes the
    colour is the one thing left amber on a kanji exercise.
    """
    offenders = []
    for line_no, line in enumerate(CSS.splitlines(), 1):
        if "--amber" in line:
            continue  # the definition itself, and the kanji override
        if ACCENT_LITERALS.search(line):
            offenders.append(f"theme.css:{line_no}: {line.strip()}")
    assert offenders == [], "accent written as a literal:\n" + "\n".join(offenders)


def test_headings_use_the_heading_classes_not_the_gauge_label():
    """`.lbl` is a gauge label; `.sec-title` is a heading.

    They were the same class, and `#dashboard .lbl { font-size: 12px }` — a rule
    about chrome text — silently captured every shelf heading by ID
    specificity. A heading inside `.sec` must never be `.lbl`.
    """
    offenders = []
    for path in TEMPLATES:
        for line_no, line in enumerate(path.read_text().splitlines(), 1):
            if '<section class="sec' in line and 'class="lbl"' in line:
                offenders.append(f"{path.name}:{line_no}: {line.strip()}")
    assert offenders == [], "section heading using the gauge label class:\n" + "\n".join(offenders)


def test_the_type_tokens_are_declared_once():
    """Sizes come from tokens so one change moves every surface together."""
    for token in (
        "--title-size",
        "--title-desc-size",
        "--title-gap",
        "--title-inset",
        "--title-space-above",
        "--title-space-below",
        "--panel-title-size",
        "--panel-desc-size",
    ):
        assert f"{token}:" in CSS, f"{token} is not declared"


def test_no_view_overrides_the_heading_type():
    """Per-view rules may change rhythm (margins), never type (font-size).

    Re-specifying the size per page is precisely how the dashboard and
    /decks drifted to different scales.
    """
    offenders = []
    pattern = re.compile(r"^#\w[\w -]*\s+\.sec-(title|desc)\s*\{([^}]*)\}", re.M)
    for match in pattern.finditer(CSS):
        if "font-size" in match.group(2):
            offenders.append(match.group(0).strip())
    assert offenders == [], "a view is overriding heading type:\n" + "\n".join(offenders)


@pytest.mark.parametrize("name", ["sec-title", "sec-desc"])
def test_the_heading_classes_are_actually_styled(name):
    assert f".{name} {{" in CSS, f".{name} has no rule"


def test_card_height_constants_agree_with_the_backs_measure():
    """`CARD_MEANING_CH` and `.back-meaning { max-width }` are the same number.

    Height is computed from how many lines the meaning wraps to. If the JS
    measure and the CSS measure disagree, the card is sized for a wrap that does
    not happen.
    """
    study = (ROOT / "static/js/study.js").read_text()
    js = re.search(r"CARD_MEANING_CH\s*=\s*(\d+)", study)
    css = re.search(r"\.back-meaning\s*\{[^}]*max-width:\s*(\d+)ch", CSS, re.S)
    assert js and css, "could not find both measures"
    assert js.group(1) == css.group(
        1
    ), f"study.js says {js.group(1)}ch, theme.css says {css.group(1)}ch"


def test_card_width_constants_match_the_type_they_measure():
    """Each width term must use the size its register is actually rendered at.

    The card is sized by `characters × type size`. When those constants drift
    from the CSS the card is sized against type that is not on it — which is how
    the Not bad set reached the 700px cap with a 40px glyph adrift in the middle
    of it, because the glyph term used 46px and the meaning term used an implied
    19.3px against a 23px render.
    """
    study = (ROOT / "static/js/study.js").read_text()

    def js(name):
        match = re.search(rf"{name}\s*=\s*([\d.]+)", study)
        assert match, f"{name} is not defined in study.js"
        return float(match.group(1))

    # The prompt on a text card.
    css_glyph = re.search(
        r'body\[data-card-size="text"\] #glyph,\s*'
        r'body\[data-card-size="text"\] #back-glyph \{[^}]*font-size:\s*(\d+)px',
        CSS,
        re.S,
    )
    assert css_glyph, "could not find the text-card glyph size"
    assert js("CARD_GLYPH_PX") == float(css_glyph.group(1))

    # The reading line.
    css_sound = re.search(r'body\[data-card-size="text"\] #back-sound \{ font-size: (\d+)px', CSS)
    assert css_sound, "could not find the text-card reading size"
    assert js("CARD_SOUND_TYPE_PX") == float(css_sound.group(1))

    # The meaning: upper bound of its clamp, and the measure it wraps at.
    css_meaning = re.search(
        r"\.back-meaning \{[^}]*font-size:\s*clamp\([^,]+,[^,]+,\s*(\d+)px\)[^}]*"
        r"max-width:\s*(\d+)ch",
        CSS,
        re.S,
    )
    assert css_meaning, "could not find .back-meaning's type and measure"
    assert js("CARD_MEANING_TYPE_PX") == float(css_meaning.group(1))
    assert js("CARD_MEANING_CH") == float(css_meaning.group(2))

    # The note, in the phrase mode these sets render in.
    css_note = re.search(
        r"\.mode-phrase \.back-note \{ max-width: (\d+)ch; font-size: (\d+)px", CSS
    )
    assert css_note, "could not find .mode-phrase .back-note"
    assert js("CARD_NOTE_CH") == float(css_note.group(1))
    assert js("CARD_NOTE_TYPE_PX") == float(css_note.group(2))


def test_no_deck_is_sized_against_text_that_wraps_anyway():
    """Widening past a register's own measure buys nothing.

    `.back-meaning` wraps at 30ch, so a 32-character gloss must not make the
    card wider than a 30-character one. Without the cap, one long meaning
    inflated the whole deck.
    """
    study = (ROOT / "static/js/study.js").read_text()
    for term, cap in (("forMeaning", "CARD_MEANING_CH"), ("forNote", "CARD_NOTE_CH")):
        line = re.search(rf"const {term} =([^;]+);", study, re.S)
        assert line, f"{term} is not computed"
        assert "Math.min(" in line.group(1) and cap in line.group(
            1
        ), f"{term} is not capped at {cap}"


def test_the_session_recap_can_always_be_scrolled_and_left():
    """A summary is worthless if you cannot reach the end of it.

    The recap grew past the viewport on a ten-card deck: the panel had no
    max-height, so it sized to its content, and the overlay centres its child —
    pushing the overflow off *both* ends where nothing scrolls. The last cards
    and the two buttons that close the session were unreachable.

    Three properties have to hold together, and they hold for **every** session
    because they are properties of the panel, not of any deck.
    """
    # 1. The panel may never exceed the overlay.
    assert re.search(
        r"\.recap-card \{[^}]*max-height:\s*100%", CSS, re.S
    ), "the recap panel has no max-height, so it will size to its content"

    # 2. The scroll area must be allowed to shrink. `min-height: 0` is the easy
    #    miss — a flex item's default minimum size is its content, so without it
    #    the area refuses to shrink and overflows whatever overflow-y says.
    scroll = re.search(r"\.recap-card > \.recap-scroll \{([^}]*)\}", CSS, re.S)
    assert scroll, "nothing overrides the `flex: 0 0 auto` on the recap's children"
    assert "min-height: 0" in scroll.group(1), "the scroll area cannot shrink"
    assert "flex: 1 1 auto" in scroll.group(1), "the scroll area cannot grow"

    # 3. Leaving must never require scrolling: the actions are a sibling of the
    #    scroll area, not a child of it. Parsed rather than pattern-matched —
    #    counting tags in a string is how a check like this quietly stops
    #    meaning anything the next time the markup is indented differently.
    from html.parser import HTMLParser

    class Nesting(HTMLParser):
        def __init__(self):
            super().__init__()
            self.stack = []
            self.inside_scroll = None

        def handle_starttag(self, tag, attrs):
            classes = dict(attrs).get("class", "").split()
            if "recap-act" in classes and self.inside_scroll is None:
                self.inside_scroll = "recap-scroll" in self.stack
            if tag not in ("input", "img", "br", "hr", "meta", "link"):
                self.stack.append(classes[0] if classes else tag)

        def handle_endtag(self, tag):
            if self.stack:
                self.stack.pop()

    parser = Nesting()
    parser.feed((ROOT / "templates/study.html").read_text())
    assert (
        parser.inside_scroll is False
    ), "the recap actions are inside the scroll area and can scroll out of reach"


def test_every_full_screen_overlay_is_bounded_by_the_window():
    """The recap's failure shape — centre a child in a viewport-sized parent —
    is shared by the other overlays, so all of them carry the same guard."""
    for selector in (".recap-card", ".help-card", ".game-done-card", ".settings-card"):
        pattern = rf"{re.escape(selector)}[^{{]*\{{[^}}]*max-height:"
        assert re.search(pattern, CSS, re.S), f"{selector} is not bounded by the window"

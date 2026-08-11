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

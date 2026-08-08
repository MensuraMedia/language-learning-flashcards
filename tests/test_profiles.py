"""Profile slugs — pure functions, no database involved."""

from __future__ import annotations

import pytest

from japanese_practice import profiles


@pytest.mark.parametrize(
    "name,expected",
    [
        ("Default", "default"),
        ("  Kenji  Sato ", "kenji-sato"),
        ("A/B test", "a-b-test"),
        ("Ünïcode", "unicode"),
    ],
)
def test_slugify(name, expected):
    assert profiles.slugify(name) == expected


def test_names_with_no_ascii_still_get_a_usable_slug():
    """A profile called ひろ is reasonable; an empty filename is not."""
    slug = profiles.slugify("ひろ")
    assert slug and slug.isascii() and "/" not in slug

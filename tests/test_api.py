"""HTTP surface and the session engine end to end.

Uses Quart's `test_app()` so `before_serving` runs — that is what opens the
database, applies the schema and seeds the content modules. These tests
therefore exercise the real startup path, not a hand-assembled one.
"""

from __future__ import annotations

import pytest
import pytest_asyncio

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def client(app):
    """A test client with the full startup lifecycle applied."""
    async with app.test_app() as running:
        yield running.test_client()


# -- views -----------------------------------------------------------------


async def test_dashboard_renders(client):
    response = await client.get("/")
    assert response.status_code == 200
    body = await response.get_data(as_text=True)
    assert 'class="view on"' in body, "the .on class is required or the page is invisible"
    assert "theme.css" in body


async def test_study_view_renders_with_the_card_scaffold(client):
    response = await client.get("/study")
    assert response.status_code == 200
    body = await response.get_data(as_text=True)
    # The stylesheet positions .card3d absolutely inside .deck3d; without that
    # chain the card collapses to zero height.
    for required in ("deck3d", "tilt", "lift", "card3d", "face front", "face back"):
        assert required in body, f"study view missing {required!r}"


async def test_front_face_markup_contains_no_reading_fields(client):
    """The front face must carry the glyph container and nothing else."""
    body = await (await client.get("/study")).get_data(as_text=True)
    front = body.split('class="face front"')[1].split('class="face back"')[0]
    for leaked in ("back-sound", "back-meaning", "back-readings", "speaker"):
        assert leaked not in front


# -- segments --------------------------------------------------------------


async def test_segments_lists_difficulties_with_live_counts(client):
    payload = await (await client.get("/api/segments")).get_json()
    segments = {s["key"]: s for s in payload["segments"]}

    assert segments["hiragana:gojuon"]["count"] == 46
    assert segments["hiragana:all"]["count"] == 104
    assert segments["katakana:all"]["count"] == 104
    assert segments["kanji:N5"]["count"] == 107


async def test_segments_expose_all_three_axes(client):
    payload = await (await client.get("/api/segments")).get_json()
    assert set(payload["challenges"]) == {
        "recognition",
        "recall",
        "timed",
        "listening",
        "mixed",
    }
    assert set(payload["scoring"]) == {"accuracy", "speed", "streak", "srs"}
    assert payload["segments"], "difficulty axis is empty"


async def test_empty_segments_are_omitted(client):
    """Difficulty keys with no seeded characters must not be offered."""
    payload = await (await client.get("/api/segments")).get_json()
    keys = {s["key"] for s in payload["segments"]}
    assert "kanji:N1" not in keys, "N1 is unseeded and should not be listed"
    assert all(s["count"] > 0 for s in payload["segments"])


# -- summary ---------------------------------------------------------------


async def test_summary_returns_every_panel_on_a_fresh_install(client):
    payload = await (await client.get("/api/summary")).get_json()
    assert payload["totals"]["attempts"] == 0
    assert payload["per_character_miss_rate"] == []
    assert len(payload["time_of_day"]) == 24


# -- session lifecycle -----------------------------------------------------


async def test_full_session_lifecycle(client):
    created = await (
        await client.post(
            "/api/session",
            json={
                "difficulty": "hiragana:gojuon",
                "challenge": "recognition",
                "scoring": "accuracy",
                "limit": 3,
            },
        )
    ).get_json()

    session_id = created["session_id"]
    cards = created["cards"]
    assert len(cards) == 3
    assert all(card["glyph"] for card in cards)

    first = await (
        await client.post(
            f"/api/session/{session_id}/attempt",
            json={"character_id": cards[0]["id"], "correct": True, "latency_ms": 800},
        )
    ).get_json()
    assert first == {
        "awarded": 10,
        "skipped": False,
        "correct": 1,
        "score": 10,
        "streak": 1,
        "total": 1,
    }

    second = await (
        await client.post(
            f"/api/session/{session_id}/attempt",
            json={
                "character_id": cards[1]["id"],
                "correct": False,
                "latency_ms": 4000,
                "streak": first["streak"],
                "given_answer": cards[2]["glyph"],
            },
        )
    ).get_json()
    assert second["awarded"] == 0
    assert second["streak"] == 0, "a wrong answer must reset the streak"
    assert second["score"] == 10

    final = await (await client.post(f"/api/session/{session_id}/end")).get_json()
    assert final["total"] == 2
    assert final["correct"] == 1
    assert final["max_streak"] == 1
    assert final["ended_at"] is not None


async def test_attempts_feed_the_analytics(client):
    created = await (
        await client.post("/api/session", json={"difficulty": "hiragana:gojuon", "limit": 2})
    ).get_json()
    cards = created["cards"]
    await client.post(
        f"/api/session/{created['session_id']}/attempt",
        json={
            "character_id": cards[0]["id"],
            "correct": False,
            "latency_ms": 3000,
            "given_answer": cards[1]["glyph"],
        },
    )

    summary = await (await client.get("/api/summary")).get_json()
    assert summary["totals"]["attempts"] == 1
    assert summary["per_character_miss_rate"][0]["glyph"] == cards[0]["glyph"]
    assert summary["confusion_pairs"][0]["mistaken_for"] == cards[1]["glyph"]


async def test_drill_path_overrides_difficulty(client):
    """Clicking a heatmap cell builds a deck from exactly those characters."""
    seed = await (
        await client.post("/api/session", json={"difficulty": "hiragana:gojuon", "limit": 3})
    ).get_json()
    wanted = [card["id"] for card in seed["cards"][:2]]

    drilled = await (await client.post("/api/session", json={"character_ids": wanted})).get_json()

    assert [card["id"] for card in drilled["cards"]] == wanted
    assert drilled["difficulty"] == "drill:custom"


async def test_scoring_scheme_is_honoured(client):
    created = await (
        await client.post(
            "/api/session",
            json={"difficulty": "hiragana:gojuon", "scoring": "streak", "limit": 2},
        )
    ).get_json()
    result = await (
        await client.post(
            f"/api/session/{created['session_id']}/attempt",
            json={"character_id": created["cards"][0]["id"], "correct": True, "streak": 4},
        )
    ).get_json()
    assert result["awarded"] == 50, "streak scheme awards 10 x streak"


# -- character detail ------------------------------------------------------


async def test_character_detail_includes_recall_history(client):
    created = await (
        await client.post("/api/session", json={"difficulty": "hiragana:gojuon", "limit": 1})
    ).get_json()
    card = created["cards"][0]
    await client.post(
        f"/api/session/{created['session_id']}/attempt",
        json={"character_id": card["id"], "correct": True, "latency_ms": 900},
    )

    payload = await (await client.get(f"/api/character/{card['id']}")).get_json()
    assert payload["character"]["glyph"] == card["glyph"]
    assert len(payload["history"]) == 1
    assert payload["history"][0]["correct"] == 1


# -- audio -----------------------------------------------------------------


async def test_audio_always_returns_playable_bytes(client):
    created = await (
        await client.post("/api/session", json={"difficulty": "hiragana:gojuon", "limit": 1})
    ).get_json()
    response = await client.get(f"/api/audio/{created['cards'][0]['id']}")

    assert response.status_code == 200
    assert response.mimetype in {"audio/wav", "audio/mpeg"}
    data = await response.get_data()
    assert len(data) > 0
    if response.mimetype == "audio/wav":
        assert data[:4] == b"RIFF"


# -- error handling --------------------------------------------------------


async def test_unknown_difficulty_is_rejected(client):
    response = await client.post("/api/session", json={"difficulty": "klingon:all"})
    assert response.status_code == 400
    assert (await response.get_json())["code"] == "invalid_request"


async def test_unknown_challenge_is_rejected(client):
    response = await client.post(
        "/api/session", json={"difficulty": "hiragana:gojuon", "challenge": "interpretive"}
    )
    assert response.status_code == 400


async def test_unknown_scoring_scheme_is_rejected(client):
    response = await client.post(
        "/api/session", json={"difficulty": "hiragana:gojuon", "scoring": "vibes"}
    )
    assert response.status_code == 400


async def test_attempt_without_character_id_is_rejected(client):
    created = await (
        await client.post("/api/session", json={"difficulty": "hiragana:gojuon", "limit": 1})
    ).get_json()
    response = await client.post(
        f"/api/session/{created['session_id']}/attempt", json={"correct": True}
    )
    assert response.status_code == 400
    assert "character_id" in (await response.get_json())["message"]


async def test_attempt_against_unknown_session_is_rejected(client):
    response = await client.post(
        "/api/session/999999/attempt", json={"character_id": 1, "correct": True}
    )
    assert response.status_code == 400


async def test_unknown_character_returns_not_found(client):
    response = await client.get("/api/character/999999")
    assert response.status_code == 404
    assert (await response.get_json())["code"] == "not_found"


async def test_audio_for_unknown_character_returns_not_found(client):
    response = await client.get("/api/audio/999999")
    assert response.status_code == 404


async def test_error_responses_share_one_shape(client):
    for request in (
        client.get("/api/character/999999"),
        client.post("/api/session", json={"difficulty": "nope:nope"}),
    ):
        payload = await (await request).get_json()
        assert set(payload) == {"code", "message"}


# -- multiple choice -------------------------------------------------------


async def test_each_card_carries_three_choices_including_the_answer(client):
    created = await (
        await client.post("/api/session", json={"difficulty": "hiragana:gojuon", "limit": 5})
    ).get_json()

    for card in created["cards"]:
        assert len(card["choices"]) == 3
        assert card["answer"] in card["choices"], "the correct option must be offered"
        assert len(set(card["choices"])) == 3, "options must be distinct"


async def test_kana_choices_are_romaji_and_kanji_choices_are_meanings(client):
    kana = await (
        await client.post("/api/session", json={"difficulty": "hiragana:gojuon", "limit": 1})
    ).get_json()
    assert kana["cards"][0]["answer"] == kana["cards"][0]["romaji"]

    kanji = await (
        await client.post("/api/session", json={"difficulty": "kanji:N5", "limit": 1})
    ).get_json()
    assert kanji["cards"][0]["answer"] == kanji["cards"][0]["meaning"]


async def test_choice_order_is_not_fixed(client):
    """A correct answer always in slot 1 would be trivially guessable."""
    positions = set()
    for _ in range(12):
        created = await (
            await client.post("/api/session", json={"difficulty": "hiragana:gojuon", "limit": 1})
        ).get_json()
        card = created["cards"][0]
        positions.add(card["choices"].index(card["answer"]))
    assert len(positions) > 1, f"answer always landed in slot(s) {positions}"


# -- skipping --------------------------------------------------------------


async def test_skip_costs_a_point_and_breaks_the_streak(client):
    created = await (
        await client.post("/api/session", json={"difficulty": "hiragana:gojuon", "limit": 3})
    ).get_json()
    sid, cards = created["session_id"], created["cards"]

    await client.post(
        f"/api/session/{sid}/attempt",
        json={"character_id": cards[0]["id"], "correct": True},
    )
    skipped = await (
        await client.post(
            f"/api/session/{sid}/attempt",
            json={"character_id": cards[1]["id"], "skipped": True, "streak": 1},
        )
    ).get_json()

    assert skipped["awarded"] == -1
    assert skipped["skipped"] is True
    assert skipped["streak"] == 0
    assert skipped["score"] == 9  # 10 for the correct card, minus 1


async def test_skip_counts_against_the_character_in_the_weakness_view(client):
    created = await (
        await client.post("/api/session", json={"difficulty": "hiragana:gojuon", "limit": 2})
    ).get_json()
    sid, cards = created["session_id"], created["cards"]

    await client.post(
        f"/api/session/{sid}/attempt",
        json={"character_id": cards[0]["id"], "skipped": True},
    )

    summary = await (await client.get("/api/summary")).get_json()
    row = summary["per_character_miss_rate"][0]
    assert row["glyph"] == cards[0]["glyph"]
    assert row["miss_rate"] == 1.0
    assert row["skipped"] == 1
    assert summary["weakest_characters"][0]["glyph"] == cards[0]["glyph"]


async def test_a_skip_is_never_counted_as_correct(client):
    created = await (
        await client.post("/api/session", json={"difficulty": "hiragana:gojuon", "limit": 2})
    ).get_json()
    sid = created["session_id"]
    await client.post(
        f"/api/session/{sid}/attempt",
        json={"character_id": created["cards"][0]["id"], "correct": True, "skipped": True},
    )
    final = await (await client.post(f"/api/session/{sid}/end")).get_json()
    assert final["correct"] == 0, "skipped must override a correct flag"

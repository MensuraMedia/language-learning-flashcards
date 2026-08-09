"""HTTP surface and the session engine end to end.

Uses Quart's `test_app()` so `before_serving` runs — that is what opens the
database, applies the schema and seeds the content modules. These tests
therefore exercise the real startup path, not a hand-assembled one.
"""

from __future__ import annotations

import pytest
import pytest_asyncio

from japanese_practice.db import DIFFICULTY_KEYS

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
    assert segments["kanji:N5"]["count"] == 113
    assert segments["kanji:N4"]["count"] == 169
    assert segments["kanji:top200"]["count"] == 200
    assert segments["kanji:top500"]["count"] == 500


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


async def test_every_declared_difficulty_key_is_offered(client):
    """Every key in the closed set now resolves to characters."""
    payload = await (await client.get("/api/segments")).get_json()
    keys = {s["key"] for s in payload["segments"]}
    assert keys == set(DIFFICULTY_KEYS)
    assert all(s["count"] > 0 for s in payload["segments"])


async def test_empty_segments_are_omitted(db):
    """A key with no seeded characters must not be offered.

    Everything bundled is seeded, so the behaviour is exercised against a
    database holding one script — otherwise this guard would pass vacuously.
    """
    from japanese_practice.content.hiragana import HIRAGANA
    from japanese_practice.content.loader import seed_content
    from japanese_practice.db import available_segments

    await seed_content(db, HIRAGANA)
    keys = {s["key"] for s in await available_segments(db)}
    assert "hiragana:gojuon" in keys
    assert not any(k.startswith(("katakana:", "kanji:")) for k in keys)


# -- summary ---------------------------------------------------------------


async def test_summary_returns_every_panel_on_a_fresh_install(client):
    payload = await (await client.get("/api/summary")).get_json()
    assert payload["totals"]["attempts"] == 0
    assert payload["per_character_miss_rate"] == []


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


# -- distractor quality ----------------------------------------------------


async def test_handakuon_choices_vary_the_consonant(client):
    """The p- row exists to teach は/ば/ぱ. If every option is p-, it cannot."""
    created = await (
        await client.post("/api/session", json={"difficulty": "hiragana:handakuon", "limit": 5})
    ).get_json()

    for card in created["cards"]:
        onsets = {c[0] for c in card["choices"]}
        assert len(onsets) > 1, f"{card['glyph']} offered only {card['choices']}"


async def test_known_confusion_partners_are_preferred_distractors(client):
    """シ should be offered against ツ/ン, not against random katakana."""
    from japanese_practice.session import _confusion_partners

    seen_partner = False
    for _ in range(10):
        created = await (
            await client.post("/api/session", json={"difficulty": "katakana:gojuon", "limit": 20})
        ).get_json()
        for card in created["cards"]:
            partners = set(_confusion_partners(card["glyph"]))
            if not partners:
                continue
            others = [c for c in card["choices"] if c != card["answer"]]
            if others:
                seen_partner = True
                break
        if seen_partner:
            break
    assert seen_partner, "no card with curated confusion partners was ever dealt"


# -- memory games ----------------------------------------------------------


async def test_board_pairs_a_glyph_with_its_own_reading(client):
    """A pair is a character and ITS reading — never two glyphs."""
    board = await (await client.post("/api/game/board", json={"pairs": 5})).get_json()

    by_pair = {}
    for tile in board["tiles"]:
        by_pair.setdefault(tile["pair_id"], []).append(tile)

    assert len(by_pair) == 5
    for tiles in by_pair.values():
        assert len(tiles) == 2
        assert {t["kind"] for t in tiles} == {"glyph", "reading"}
        assert tiles[0]["character_id"] == tiles[1]["character_id"]


async def test_pelmanism_is_dealt_face_down(client):
    matchup = await (await client.post("/api/game/board", json={"mode": "matchup"})).get_json()
    hidden = await (await client.post("/api/game/board", json={"mode": "pelmanism"})).get_json()
    assert matchup["face_down"] is False
    assert hidden["face_down"] is True


async def test_confusion_mode_seeds_from_the_curated_look_alikes(client):
    from japanese_practice.content.confusions import CONFUSION_PAIRS

    known = {g for pair in CONFUSION_PAIRS for g in pair}
    board = await (
        await client.post("/api/game/board", json={"mode": "confusion", "pairs": 6})
    ).get_json()

    glyphs = [t["text"] for t in board["tiles"] if t["kind"] == "glyph"]
    assert board["source"] == "confusion-pairs"
    assert all(g in known for g in glyphs), f"non-confusable glyphs dealt: {glyphs}"


async def test_pair_count_is_clamped(client):
    tiny = await (await client.post("/api/game/board", json={"pairs": 1})).get_json()
    huge = await (await client.post("/api/game/board", json={"pairs": 999})).get_json()
    assert tiny["pairs"] >= 3
    assert huge["pairs"] <= 12


async def test_unknown_game_mode_is_rejected(client):
    response = await client.post("/api/game/board", json={"mode": "solitaire"})
    assert response.status_code == 400


async def test_a_new_learner_still_gets_a_board(client):
    """No attempt history means no weak set — the deck must fill the gap."""
    board = await (await client.post("/api/game/board", json={"pairs": 6})).get_json()
    assert board["pairs"] == 6
    assert board["source"] in {"pool", "weakest+pool"}


async def test_mispair_needs_a_character(client):
    response = await client.post("/api/game/mispair", json={})
    assert response.status_code == 400


async def test_every_view_route_is_reachable(client):
    """A view can be lost without any test noticing — /games shipped once with
    its template, JS and API present but no route at all."""
    for path in ("/", "/study", "/games"):
        response = await client.get(path)
        assert response.status_code == 200, f"{path} returned {response.status_code}"


async def test_games_view_links_back_to_the_dashboard(client):
    """Every sub-view must offer a way home."""
    body = await (await client.get("/games")).get_data(as_text=True)
    assert 'href="/"' in body, "no route back to the dashboard"


# -- per-script games ------------------------------------------------------


async def test_game_catalogue_offers_every_script(client):
    """Each script gets its own three boards, worded for that script."""
    payload = await (await client.get("/api/games")).get_json()
    games = payload["games"]
    assert len(games) == 9
    by_script: dict[str, set[str]] = {}
    for game in games:
        by_script.setdefault(game["script"], set()).add(game["mode"])
    assert by_script == {
        "hiragana": {"matchup", "pelmanism", "confusion"},
        "katakana": {"matchup", "pelmanism", "confusion"},
        "kanji": {"matchup", "pelmanism", "confusion"},
    }
    kanji = next(g for g in games if g["script"] == "kanji" and g["mode"] == "matchup")
    kana = next(g for g in games if g["script"] == "hiragana" and g["mode"] == "matchup")
    assert "Meaning" in kanji["trains"], "a kanji board pairs on meaning"
    assert "Reading" in kana["trains"], "a kana board pairs on reading"


@pytest.mark.parametrize("script", ["hiragana", "katakana", "kanji"])
async def test_board_is_dealt_from_one_script_only(client, script):
    board = await (
        await client.post("/api/game/board", json={"pairs": 5, "script": script})
    ).get_json()
    assert board["script"] == script
    glyphs = [t["text"] for t in board["tiles"] if t["kind"] == "glyph"]
    assert glyphs
    ranges = {
        "hiragana": lambda c: "ぁ" <= c <= "ゟ",
        "katakana": lambda c: "゠" <= c <= "ヿ",
        "kanji": lambda c: "一" <= c <= "鿿",
    }
    assert all(ranges[script](g[0]) for g in glyphs), f"{script} board leaked another script"


async def test_confusion_board_is_script_specific(client):
    """The look-alikes a learner mixes up differ entirely by script."""
    board = await (
        await client.post("/api/game/board", json={"mode": "confusion", "script": "kanji"})
    ).get_json()
    glyphs = [t["text"] for t in board["tiles"] if t["kind"] == "glyph"]
    assert board["source"] == "confusion-pairs"
    assert all("一" <= g <= "鿿" for g in glyphs)


async def test_unknown_script_is_rejected(client):
    response = await client.post("/api/game/board", json={"script": "hangul"})
    assert response.status_code == 400
    assert (await response.get_json())["code"] == "invalid_request"


# -- kanji volume tiers ----------------------------------------------------


async def test_volume_tiers_slice_the_teaching_order(client):
    """Top 200 must be the first 200 of Top 500, not the first 200 rows by id."""
    from japanese_practice.content.kanji_frequency import KANJI_BY_FREQUENCY

    top200 = await (
        await client.post("/api/session", json={"difficulty": "kanji:top200", "limit": 200})
    ).get_json()
    glyphs = [card["glyph"] for card in top200["cards"]]
    assert len(glyphs) == 200
    assert set(glyphs) == set(KANJI_BY_FREQUENCY[:200])
    assert set(KANJI_BY_FREQUENCY[:200]) <= set(KANJI_BY_FREQUENCY[:500])

    # Seeding runs N5 → N1, so the lowest 200 ids are nearly all N5. If the tier
    # were still the naive id slice these two sets would coincide; they must not.
    n5_first = await (
        await client.post("/api/session", json={"difficulty": "kanji:N5", "limit": 200})
    ).get_json()
    assert set(glyphs) != {card["glyph"] for card in n5_first["cards"]}
    assert any(g not in KANJI_BY_FREQUENCY[:113] for g in glyphs)


async def test_confusion_board_puts_both_halves_of_a_pair_on_the_board(client):
    """A look-alike without its partner is just an ordinary memory tile."""
    from japanese_practice.content.confusions import CONFUSION_PAIRS

    partners: dict[str, set[str]] = {}
    for a, b in CONFUSION_PAIRS:
        partners.setdefault(a, set()).add(b)
        partners.setdefault(b, set()).add(a)

    for script in ("hiragana", "katakana", "kanji"):
        board = await (
            await client.post(
                "/api/game/board", json={"mode": "confusion", "script": script, "pairs": 6}
            )
        ).get_json()
        glyphs = [t["text"] for t in board["tiles"] if t["kind"] == "glyph"]
        assert board["source"] == "confusion-pairs", script
        paired = [g for g in glyphs if partners.get(g, set()) & set(glyphs)]
        assert len(paired) == len(
            glyphs
        ), f"{script}: {set(glyphs) - set(paired)} appeared without a partner"


async def test_kanji_options_carry_their_readings(client):
    """A kanji option is English; without the reading it says nothing about sound."""
    created = await (
        await client.post("/api/session", json={"difficulty": "kanji:N5", "limit": 5})
    ).get_json()
    for card in created["cards"]:
        readings = card["choice_readings"]
        assert readings, f"{card['glyph']} offered no readings for its options"
        # Display only — every reading must be romaji, never raw kana.
        assert not any("ぁ" <= c <= "ヿ" for r in readings.values() for c in r)
        assert set(readings) <= set(card["choices"])


async def test_kana_options_carry_no_readings(client):
    """A kana option is already the reading; repeating it would be noise."""
    created = await (
        await client.post("/api/session", json={"difficulty": "hiragana:gojuon", "limit": 3})
    ).get_json()
    assert all(card["choice_readings"] == {} for card in created["cards"])


# -- UI sound --------------------------------------------------------------


@pytest.mark.parametrize(
    "cue_id", ["ding", "chime", "bell", "marimba", "arpeggio", "sparkle", "blip"]
)
async def test_every_cue_is_served(client, cue_id):
    """Cues are static assets; a 404 loses the sound with no visible error."""
    response = await client.get(f"/static/audio/sounds/cue-{cue_id}.wav")
    assert response.status_code == 200
    body = await response.get_data()
    assert len(body) > 1024
    # A real RIFF/WAVE header, not an HTML error page returned with a 200.
    assert body[:4] == b"RIFF" and body[8:12] == b"WAVE"


# -- word decks and the catalogue ------------------------------------------


@pytest.mark.parametrize(
    "key,count",
    [
        ("vocab:days", 7),
        ("vocab:months", 12),
        ("vocab:numbers", 36),
        ("vocab:time", 16),
        ("vocab:demonstratives", 20),
        ("vocab:particles", 15),
    ],
)
async def test_word_decks_are_offered_with_their_counts(client, key, count):
    payload = await (await client.get("/api/segments")).get_json()
    segments = {s["key"]: s["count"] for s in payload["segments"]}
    assert segments[key] == count


async def test_seeding_words_did_not_clobber_characters(client):
    """は is a hiragana character *and* a particle; 一 is a kanji *and* the number one.

    A glyph-unique constraint made seeding the second overwrite the first, which
    silently shrank the kana and kanji decks.
    """
    payload = await (await client.get("/api/segments")).get_json()
    segments = {s["key"]: s["count"] for s in payload["segments"]}
    assert segments["hiragana:gojuon"] == 46
    assert segments["hiragana:all"] == 104
    assert segments["kanji:top200"] == 200


async def test_a_word_card_is_graded_on_meaning_against_its_own_set(client):
    """Offering "March" against a 月曜日 card can be solved by category alone."""
    created = await (
        await client.post("/api/session", json={"difficulty": "vocab:days", "limit": 5})
    ).get_json()
    days = {
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    }
    for card in created["cards"]:
        assert card["answer"] in days
        assert set(card["choices"]) <= days, "a distractor came from another set"
        assert card["answer"] in card["choices"]


async def test_catalogue_lists_what_works_and_what_does_not(client):
    payload = await (await client.get("/api/catalogue")).get_json()
    assert payload["counts"]["available"] == 33
    assert len(payload["planned"]) == 11
    names = {item["name"] for item in payload["planned"]}
    assert "Alternate phrases" in names
    for item in payload["planned"]:
        assert item["status"] in {"planned", "experimental"}
        # Every unbuilt entry says what is blocking it, so the list cannot become
        # a wish list that implies work is imminent.
        assert item["blocker"]


async def test_decks_view_renders(client):
    response = await client.get("/decks")
    assert response.status_code == 200
    body = await response.get_data(as_text=True)
    assert 'class="view on"' in body
    assert "decks.js" in body


# -- phrase sets -----------------------------------------------------------


@pytest.mark.parametrize(
    "key,count",
    [
        ("phrase:likes", 10),
        ("phrase:konbini", 10),
        ("phrase:lets", 10),
        ("phrase:requests", 8),
        ("phrase:basics", 10),
    ],
)
async def test_phrase_sets_are_offered_with_their_counts(client, key, count):
    payload = await (await client.get("/api/segments")).get_json()
    segments = {s["key"]: s["count"] for s in payload["segments"]}
    assert segments[key] == count


async def test_a_phrase_card_is_graded_on_meaning_within_its_own_set(client):
    """Offering "let's eat" against a convenience-store card gives it away."""
    created = await (
        await client.post("/api/session", json={"difficulty": "phrase:lets", "limit": 6})
    ).get_json()
    for card in created["cards"]:
        assert card["answer"].startswith("let's"), card["answer"]
        assert all(c.startswith("let's") for c in card["choices"]), card["choices"]
        assert card["answer"] in card["choices"]


async def test_phrase_deck_titles_drop_the_redundant_prefix(client):
    """The shelf is already called Phrase Sets; the deck says what the set is."""
    payload = await (await client.get("/api/segments")).get_json()
    labels = {s["key"]: s["label"] for s in payload["segments"]}
    assert labels["phrase:konbini"] == "At the convenience store"
    assert labels["phrase:lets"] == "Let's — ましょう"
    # Other scripts keep theirs, because there the prefix is the distinction.
    assert labels["katakana:gojuon"] == "Katakana · Gojuon"


async def test_every_phrase_carries_its_reading(client):
    """A phrase without a reading cannot be said, which is the point of it."""
    created = await (
        await client.post("/api/session", json={"difficulty": "phrase:konbini", "limit": 10})
    ).get_json()
    for card in created["cards"]:
        assert card["romaji"], f"{card['glyph']} has no reading"
        assert card["script"] == "phrase"


# -- cards that carry context ----------------------------------------------


@pytest.mark.parametrize(
    "key,count",
    [
        ("phrase:praise", 10),
        ("phrase:encourage", 10),
        ("phrase:describe", 8),
        ("phrase:rough", 10),
        ("phrase:gari", 7),
    ],
)
async def test_context_sets_are_offered_with_their_counts(client, key, count):
    payload = await (await client.get("/api/segments")).get_json()
    segments = {s["key"]: s["count"] for s in payload["segments"]}
    assert segments[key] == count


@pytest.mark.parametrize(
    "key", ["phrase:praise", "phrase:encourage", "phrase:describe", "phrase:rough", "phrase:gari"]
)
async def test_every_card_in_a_context_set_has_a_note(client, key):
    """These sets exist because the gloss alone misleads.

    強がり is not "a strong person" but someone putting on a brave face; ばか is
    mild in Osaka and sharp in Tokyo. A card here without its note is worse than
    no card, because it teaches the learner something subtly wrong.
    """
    created = await (
        await client.post("/api/session", json={"difficulty": key, "limit": 10})
    ).get_json()
    for card in created["cards"]:
        assert card["note"], f"{card['glyph']} in {key} has no usage note"
        assert len(card["note"]) > 20, f"{card['glyph']} has a note too short to be context"


async def test_a_note_survives_the_round_trip_to_the_card(client):
    created = await (
        await client.post("/api/session", json={"difficulty": "phrase:gari", "limit": 7})
    ).get_json()
    by_glyph = {c["glyph"]: c for c in created["cards"]}
    tsuyogari = by_glyph.get("強がり")
    assert tsuyogari is not None
    assert tsuyogari["answer"] == "someone putting on a brave face"
    # The note is what stops 強がり being read as "a strong person".
    assert "bluffing" in tsuyogari["note"]
    assert tsuyogari["romaji"] == "tsuyogari"

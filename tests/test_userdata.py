"""Profiles, export/import and reset — the settings surface."""

from __future__ import annotations

import pytest
import pytest_asyncio

from japanese_practice import profiles

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def client(app):
    async with app.test_app() as running:
        yield running.test_client()


async def _one_session(client, correct=True):
    created = await (
        await client.post("/api/session", json={"difficulty": "hiragana:gojuon", "limit": 2})
    ).get_json()
    for card in created["cards"]:
        await client.post(
            f"/api/session/{created['session_id']}/attempt",
            json={"character_id": card["id"], "correct": correct, "latency_ms": 900},
        )
    await client.post(f"/api/session/{created['session_id']}/end")
    return created


# -- export / import -------------------------------------------------------


async def test_export_keys_rows_by_glyph_not_id(client):
    """Ids move when seed order changes; glyphs do not."""
    await _one_session(client)
    payload = await (await client.get("/api/data/export")).get_json()

    assert payload["format"] == "japanese-practice/progress"
    assert payload["counts"]["attempts"] == 2
    assert all("glyph" in row for row in payload["attempts"])
    assert all("character_id" not in row for row in payload["attempts"])


async def test_export_round_trips_through_import(client):
    await _one_session(client)
    exported = await (await client.get("/api/data/export")).get_json()
    before = await (await client.get("/api/summary")).get_json()

    await client.post("/api/data/reset", json={"confirm": True})
    emptied = await (await client.get("/api/summary")).get_json()
    assert emptied["totals"]["attempts"] == 0

    result = await (await client.post("/api/data/import", json={"payload": exported})).get_json()
    assert result["attempts"] == 2
    assert result["skipped_unknown_glyphs"] == 0

    after = await (await client.get("/api/summary")).get_json()
    assert after["totals"]["attempts"] == before["totals"]["attempts"]
    assert after["totals"]["accuracy"] == before["totals"]["accuracy"]


async def test_import_rejects_a_foreign_document(client):
    response = await client.post("/api/data/import", json={"payload": {"format": "anki"}})
    assert response.status_code == 400


async def test_import_rejects_an_unreadable_version(client):
    response = await client.post(
        "/api/data/import",
        json={"payload": {"format": "japanese-practice/progress", "version": 99}},
    )
    assert response.status_code == 400
    assert "version" in (await response.get_json())["message"]


async def test_import_skips_glyphs_this_build_does_not_have(client):
    """An export from a build with more characters must still restore what it can."""
    await _one_session(client)
    exported = await (await client.get("/api/data/export")).get_json()
    exported["attempts"].append({**exported["attempts"][0], "glyph": "𠮷"})

    result = await (await client.post("/api/data/import", json={"payload": exported})).get_json()
    assert result["skipped_unknown_glyphs"] == 1
    assert result["attempts"] == 2


# -- reset -----------------------------------------------------------------


async def test_reset_requires_explicit_confirmation(client):
    await _one_session(client)
    response = await client.post("/api/data/reset", json={})
    assert response.status_code == 400
    assert (await response.get_json())["code"] == "confirm_required"

    summary = await (await client.get("/api/summary")).get_json()
    assert summary["totals"]["attempts"] == 2, "an unconfirmed reset must change nothing"


async def test_reset_clears_progress_but_keeps_the_characters(client):
    await _one_session(client)
    result = await (await client.post("/api/data/reset", json={"confirm": True})).get_json()
    assert result["cleared"]["attempts"] == 2

    segments = await (await client.get("/api/segments")).get_json()
    assert segments["segments"], "reset must not delete the seeded content"

    summary = await (await client.get("/api/summary")).get_json()
    assert summary["totals"]["attempts"] == 0
    assert summary["per_character_miss_rate"] == []


async def test_reset_reports_what_it_removed(client):
    """A destructive action that reports nothing looks like one that failed."""
    result = await (await client.post("/api/data/reset", json={"confirm": True})).get_json()
    assert result["cleared"]["attempts"] == 0


# -- profiles --------------------------------------------------------------


async def test_default_profile_is_active_on_a_fresh_install(client):
    payload = await (await client.get("/api/profiles")).get_json()
    assert payload["active"] == profiles.DEFAULT_SLUG
    assert [p["slug"] for p in payload["profiles"]] == [profiles.DEFAULT_SLUG]


async def test_profiles_keep_separate_histories(client):
    """The whole point: one learner's attempts must not appear in another's."""
    await _one_session(client)

    created = await (await client.post("/api/profiles", json={"name": "Kenji"})).get_json()
    assert created["slug"] == "kenji"

    fresh = await (await client.get("/api/summary")).get_json()
    assert fresh["totals"]["attempts"] == 0, "a new profile starts empty"

    await client.post("/api/profiles/activate", json={"slug": "default"})
    back = await (await client.get("/api/summary")).get_json()
    assert back["totals"]["attempts"] == 2, "switching back must restore the history"


async def test_duplicate_profile_names_are_rejected(client):
    await client.post("/api/profiles", json={"name": "Kenji"})
    response = await client.post("/api/profiles", json={"name": "kenji"})
    assert response.status_code == 400


async def test_a_profile_needs_a_name(client):
    response = await client.post("/api/profiles", json={"name": "   "})
    assert response.status_code == 400


async def test_the_active_profile_cannot_be_deleted(client):
    await client.post("/api/profiles", json={"name": "Kenji"})
    response = await client.delete("/api/profiles/kenji")
    assert response.status_code == 400


async def test_the_default_profile_cannot_be_deleted(client):
    response = await client.delete("/api/profiles/default")
    assert response.status_code == 400


async def test_deleting_a_profile_removes_its_database(client, app):
    await client.post("/api/profiles", json={"name": "Kenji"})
    await _one_session(client)
    path = profiles.path_for(app.config["JP_CONFIG"], "kenji")
    assert path.exists()

    await client.post("/api/profiles/activate", json={"slug": "default"})
    await client.delete("/api/profiles/kenji")

    assert not path.exists()
    remaining = await (await client.get("/api/profiles")).get_json()
    assert [p["slug"] for p in remaining["profiles"]] == ["default"]


async def test_creating_a_profile_reports_it_as_active(client):
    """The response is what the UI renders, so it must reflect the switch."""
    created = await (await client.post("/api/profiles", json={"name": "Aya"})).get_json()
    assert created["active"] is True


# -- preferences -----------------------------------------------------------


async def test_preferences_start_empty_and_round_trip(client):
    """Settings live server-side: the webview's localStorage drops writes."""
    assert await (await client.get("/api/preferences")).get_json() == {}

    saved = await (
        await client.put("/api/preferences", json={"jp.cue": "marimba", "jp.pace": "3"})
    ).get_json()
    assert saved["saved"] == ["jp.cue", "jp.pace"]

    stored = await (await client.get("/api/preferences")).get_json()
    assert stored == {"jp.cue": "marimba", "jp.pace": "3"}


async def test_preferences_merge_rather_than_replace(client):
    await client.put("/api/preferences", json={"jp.cue": "bell"})
    await client.put("/api/preferences", json={"jp.sound": "off"})
    stored = await (await client.get("/api/preferences")).get_json()
    assert stored == {"jp.cue": "bell", "jp.sound": "off"}


async def test_unknown_preference_keys_are_rejected(client):
    """An open key-value store reachable from the page is a liability."""
    response = await client.put("/api/preferences", json={"evil": "1"})
    assert response.status_code == 400
    assert "unknown" in (await response.get_json())["message"]
    assert await (await client.get("/api/preferences")).get_json() == {}


async def test_oversized_preference_values_are_rejected(client):
    response = await client.put("/api/preferences", json={"jp.cue": "x" * 500})
    assert response.status_code == 400


async def test_preferences_accept_post_for_sendbeacon(client):
    """navigator.sendBeacon flushes queued settings on close and can only POST."""
    response = await client.post("/api/preferences", json={"jp.voice": "male"})
    assert response.status_code == 200
    stored = await (await client.get("/api/preferences")).get_json()
    assert stored["jp.voice"] == "male"


async def test_preferences_are_per_profile(client):
    """Two learners on one machine must not share a pace or a sound."""
    await client.put("/api/preferences", json={"jp.cue": "sparkle"})

    await client.post("/api/profiles", json={"name": "Aya"})
    assert await (await client.get("/api/preferences")).get_json() == {}
    await client.put("/api/preferences", json={"jp.cue": "blip"})

    await client.post("/api/profiles/activate", json={"slug": "default"})
    stored = await (await client.get("/api/preferences")).get_json()
    assert stored["jp.cue"] == "sparkle", "the other profile's choice leaked in"

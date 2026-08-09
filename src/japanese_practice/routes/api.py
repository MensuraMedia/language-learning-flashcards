"""JSON API.

Every error response is ``{"code", "message"}`` with an appropriate status.
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from quart import Blueprint, Response, current_app, jsonify, request

from .. import analytics, audio, games, profiles, tts_voicevox, userdata
from .. import session as session_engine
from ..db import Database, available_segments, get_character
from ..kana import to_romaji

log = logging.getLogger(__name__)


def get_db() -> Database:
    """The live database handle.

    Resolved from ``current_app`` rather than imported from :mod:`..app`, which
    would be a circular import — ``app`` registers this blueprint.
    """
    db: Database | None = current_app.config.get("JP_DB")
    if db is None:  # pragma: no cover - only reachable before serving starts
        raise RuntimeError("database is not initialised")
    return db


api_bp = Blueprint("api", __name__, url_prefix="/api")


def _error(code: str, message: str, status: int) -> tuple[Response, int]:
    return jsonify({"code": code, "message": message}), status


def _card(
    character: Any,
    choices: list[str] | None = None,
    choice_readings: dict[str, str] | None = None,
) -> dict[str, Any]:
    """A character as the study view needs it — front and back separated."""
    return {
        "choices": choices or [],
        # Display-only: how each option's character sounds. Grading still
        # compares the option text against `answer`.
        "choice_readings": choice_readings or {},
        "answer": session_engine.answer_text(character),
        "id": character.id,
        "glyph": character.glyph,
        "script": character.script,
        "romaji": character.romaji,
        "meaning": character.meaning,
        "onyomi": character.onyomi,
        "kunyomi": character.kunyomi,
        # A kanji card is graded on its meaning, so its options are English and
        # the kana readings are pure reference — useless to a learner who cannot
        # read them yet. Send the transliteration with them.
        "onyomi_romaji": to_romaji(character.onyomi),
        "kunyomi_romaji": to_romaji(character.kunyomi),
        "kana_group": character.kana_group,
        "jlpt_level": character.jlpt_level,
    }


@api_bp.get("/summary")
async def summary() -> Response:
    """Everything the dashboard renders, in one round trip."""
    return jsonify(await analytics.dashboard_summary(get_db()))


@api_bp.get("/credits")
async def credits() -> Response:
    """Attribution for whichever audio provider is actually in use.

    VOICEVOX requires visible credit naming the speaker. This endpoint reports
    what must be shown, so the UI never has to guess or hard-code it.
    """
    voicevox = await tts_voicevox.is_available()
    return jsonify(
        {
            "provider": "voicevox" if voicevox else "bundled",
            "required": (
                [tts_voicevox.credit("female"), tts_voicevox.credit("male")] if voicevox else []
            ),
        }
    )


@api_bp.get("/segments")
async def segments() -> Response:
    """Available exercise segments across all three axes."""
    db = get_db()
    return jsonify(
        {
            "segments": await available_segments(db),
            "challenges": list(session_engine.CHALLENGES),
            "scoring": ["accuracy", "speed", "streak", "srs"],
        }
    )


@api_bp.post("/session")
async def create_session() -> Any:
    """Start a session. ``character_ids`` overrides ``difficulty`` (drill path)."""
    body = await request.get_json(silent=True) or {}
    challenge = body.get("challenge", "recognition")
    scoring = body.get("scoring", "accuracy")
    character_ids = body.get("character_ids") or None
    difficulty = "drill:custom" if character_ids else body.get("difficulty", "")

    db = get_db()
    try:
        record = await session_engine.start_session(db, challenge, scoring, difficulty)
        cards = await session_engine.build_deck(
            db,
            difficulty,
            challenge,
            limit=int(body.get("limit", session_engine.DEFAULT_DECK_LIMIT)),
            character_ids=character_ids,
        )
    except ValueError as exc:
        return _error("invalid_request", str(exc), 400)

    if not cards:
        return _error("empty_deck", f"no characters for {difficulty!r}", 404)

    payload = []
    for card in cards:
        choices = await session_engine.build_choices(db, card)
        readings = await session_engine.choice_readings(db, card.script, choices)
        payload.append(_card(card, choices, readings))

    return jsonify(
        {
            "session_id": record.id,
            "challenge": challenge,
            "scoring": scoring,
            "difficulty": difficulty,
            "cards": payload,
        }
    )


@api_bp.post("/session/<int:session_id>/attempt")
async def record_attempt(session_id: int) -> Any:
    """Record one answer and return the running totals."""
    body = await request.get_json(silent=True) or {}
    if "character_id" not in body:
        return _error("invalid_request", "character_id is required", 400)
    try:
        result = await session_engine.record_attempt(
            get_db(),
            session_id,
            int(body["character_id"]),
            bool(body.get("correct", False)),
            latency_ms=body.get("latency_ms"),
            given_answer=body.get("given_answer"),
            streak=int(body.get("streak", 0)),
            skipped=bool(body.get("skipped", False)),
        )
    except ValueError as exc:
        return _error("invalid_request", str(exc), 400)
    return jsonify(result)


@api_bp.post("/session/<int:session_id>/end")
async def end_session(session_id: int) -> Any:
    """Finalise a session."""
    try:
        record = await session_engine.end_session(get_db(), session_id)
    except ValueError as exc:
        return _error("not_found", str(exc), 404)
    return jsonify(asdict(record))


# -- preferences ------------------------------------------------------------
#
# Interface settings live on the server rather than in the browser. The desktop
# webview accepts localStorage writes and silently drops them, so a preference
# set on the dashboard never reached the study view — a full page navigation
# starts a fresh JS context with nothing to read.


#: Only these keys are accepted. An open key-value store reachable from the page
#: is a way to fill someone's database with whatever a bug decides to write.
ALLOWED_PREFERENCES = frozenset(
    {"jp.sound", "jp.cue", "jp.volume", "jp.muted", "jp.voice", "jp.pace"}
)
MAX_PREFERENCE_LENGTH = 64


@api_bp.get("/preferences")
async def preferences_get() -> Response:
    """Every stored preference for the active profile."""
    rows = await get_db().fetch_all("SELECT key, value FROM preferences")
    return jsonify({row["key"]: row["value"] for row in rows})


# POST as well as PUT: navigator.sendBeacon, which flushes queued settings as the
# window closes, can only issue a POST.
@api_bp.route("/preferences", methods=["PUT", "POST"])
async def preferences_put() -> Any:
    """Merge a set of preferences. Unknown keys are rejected, not ignored."""
    body = await request.get_json(silent=True) or {}
    if not isinstance(body, dict):
        return _error("invalid_request", "expected an object of key/value pairs", 400)

    unknown = sorted(set(body) - ALLOWED_PREFERENCES)
    if unknown:
        return _error("invalid_request", f"unknown preference(s): {', '.join(unknown)}", 400)

    too_long = [k for k, v in body.items() if len(str(v)) > MAX_PREFERENCE_LENGTH]
    if too_long:
        return _error("invalid_request", f"value too long: {', '.join(sorted(too_long))}", 400)

    now = datetime.now(tz=timezone.utc).isoformat()
    await get_db().execute_many(
        """
        INSERT INTO preferences (key, value, updated_at) VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value,
                                       updated_at = excluded.updated_at
        """,
        [(key, str(value), now) for key, value in body.items()],
    )
    return jsonify({"saved": sorted(body)})


# -- profiles and user data -------------------------------------------------


def _config() -> Any:
    return current_app.config["JP_CONFIG"]


@api_bp.get("/profiles")
async def profile_list() -> Response:
    """Every profile, with the active one flagged."""
    cfg = _config()
    return jsonify(
        {
            "active": profiles.active_slug(cfg),
            "profiles": [p.as_dict() for p in profiles.list_profiles(cfg)],
        }
    )


@api_bp.post("/profiles")
async def profile_create() -> Any:
    """Register a profile and switch to it."""
    body = await request.get_json(silent=True) or {}
    try:
        profile = profiles.create(_config(), str(body.get("name", "")))
        await current_app.config["JP_OPEN_PROFILE"](current_app._get_current_object(), profile.slug)
        # Re-read after activation: the object from create() predates the switch
        # and would report active=false for the profile now in use.
        profile = profiles.resolve(_config(), profile.slug)
    except ValueError as exc:
        return _error("invalid_request", str(exc), 400)
    return jsonify(profile.as_dict())


@api_bp.post("/profiles/activate")
async def profile_activate() -> Any:
    """Switch profiles, reopening the database on the new one."""
    body = await request.get_json(silent=True) or {}
    slug = str(body.get("slug", ""))
    try:
        profiles.resolve(_config(), slug)
        await current_app.config["JP_OPEN_PROFILE"](current_app._get_current_object(), slug)
    except ValueError as exc:
        return _error("invalid_request", str(exc), 400)
    return jsonify({"active": slug})


@api_bp.delete("/profiles/<slug>")
async def profile_delete(slug: str) -> Any:
    """Forget a profile and delete its database."""
    try:
        profiles.delete(_config(), slug)
    except ValueError as exc:
        return _error("invalid_request", str(exc), 400)
    return jsonify({"deleted": slug})


@api_bp.get("/data/summary")
async def data_summary() -> Response:
    """What a reset would remove, so the confirmation can be specific."""
    return jsonify(await userdata.summarise(get_db()))


@api_bp.get("/data/export")
async def data_export() -> Response:
    """The active profile's progress as a portable document."""
    payload = await userdata.export_progress(get_db())
    slug = profiles.active_slug(_config())
    stamp = payload["exported_at"][:10]
    response = jsonify(payload)
    response.headers["Content-Disposition"] = (
        f'attachment; filename="japanese-practice-{slug}-{stamp}.json"'
    )
    return response


@api_bp.post("/data/import")
async def data_import() -> Any:
    """Load an export back into the active profile."""
    body = await request.get_json(silent=True) or {}
    payload = body.get("payload")
    if not isinstance(payload, dict):
        return _error("invalid_request", "no progress document supplied", 400)
    try:
        result = await userdata.import_progress(
            get_db(), payload, replace=bool(body.get("replace", True))
        )
    except ValueError as exc:
        return _error("invalid_request", str(exc), 400)
    return jsonify(result)


@api_bp.post("/data/reset")
async def data_reset() -> Any:
    """Wipe the active profile's progress. Characters are content and stay."""
    body = await request.get_json(silent=True) or {}
    if body.get("confirm") is not True:
        return _error("confirm_required", "a reset must be confirmed explicitly", 400)
    return jsonify(await userdata.reset_progress(get_db()))


@api_bp.get("/heatmap")
async def heatmap() -> Any:
    """One difficulty key's characters with their miss rates, seen or not."""
    key = request.args.get("difficulty", "hiragana:gojuon")
    try:
        return jsonify(await analytics.character_grid(get_db(), key))
    except ValueError as exc:
        return _error("invalid_request", str(exc), 400)


#: Exercises that are designed but not built. Listed rather than hidden, because
#: a catalogue that shows only what works tells a learner nothing about where the
#: app is going — and hiding them invites the same question every few weeks.
#: Every one of these is a roadmap item with acceptance criteria in ROADMAP.md.
PLANNED_DECKS: tuple[dict[str, str], ...] = (
    {
        "name": "More phrase sets",
        "jp": "フレーズ",
        "detail": (
            "Five pattern sets ship today. Next: at the station, ordering food, "
            "small talk, and the casual counterparts of 〜ましょう and 〜てください"
        ),
        "status": "planned",
        "blocker": (
            "Each new set has to be either rule-governed or a small stock every "
            "course teaches the same way. Open phrase vocabulary stays out until "
            "it can be sourced rather than recalled"
        ),
    },
    {
        "name": "Expressions",
        "jp": "表現",
        "detail": "Set expressions whose meaning is not the sum of their parts",
        "status": "planned",
        "blocker": "Same sourcing gap as Phrases",
    },
    {
        "name": "Verbs",
        "jp": "動詞",
        "detail": "Dictionary form, -masu, -te, past — the conjugation a sentence needs",
        "status": "planned",
        "blocker": "Conjugation is a generator, not a card list; needs its own exercise type",
    },
    {
        "name": "Alternate phrases",
        "jp": "言い換え",
        "detail": (
            "Many ways to say one thing — thanks as ありがとう / どうも / "
            "感謝します, sorry as すみません / ごめん / 失礼します, and the same "
            "again for interest, agreement and liking something"
        ),
        "status": "experimental",
        "blocker": (
            "Needs a card type that grades a *set* of right answers, not one. "
            "The engine currently has exactly one correct option per card"
        ),
    },
    {
        "name": "Politeness registers",
        "jp": "敬語",
        "detail": (
            "One meaning across casual, polite and humble — 食べる / 食べます / "
            "いただきます. Choosing the wrong register is the mistake that gets "
            "noticed"
        ),
        "status": "planned",
        "blocker": "Depends on Alternate phrases: it is the same one-to-many problem",
    },
    {
        "name": "Reactions",
        "jp": "相槌",
        "detail": (
            "あいづち — へえ, なるほど, そうですね. The short responses that show "
            "you are listening, and whose absence sounds cold"
        ),
        "status": "planned",
        "blocker": "A sourced list; the reference worksheets do not cover conversation",
    },
    {
        "name": "Word combinations",
        "jp": "複合語",
        "detail": "Compounds and collocations — words that travel together",
        "status": "experimental",
        "blocker": "Can be derived from the seeded kanji, but the pairings need checking",
    },
    {
        "name": "Counters",
        "jp": "助数詞",
        "detail": "本, 枚, 匹, 人 — the classifier a number takes depends on the thing",
        "status": "experimental",
        "blocker": "A closed set and safe to author; not yet written",
    },
    {
        "name": "Adjectives",
        "jp": "形容詞",
        "detail": "い- and な-adjectives, and how each one attaches",
        "status": "planned",
        "blocker": "Needs a sourced list",
    },
    {
        "name": "Typed recall",
        "jp": "入力",
        "detail": "Type the reading instead of picking it — no 33% chance floor",
        "status": "experimental",
        "blocker": "Roadmap M1. The scoring is ready; the input mode is not",
    },
    {
        "name": "Listening",
        "jp": "聞き取り",
        "detail": "Audio plays, no glyph shown — pick what you heard",
        "status": "experimental",
        "blocker": "Roadmap M7. The clip library and endpoint already exist",
    },
)


@api_bp.get("/catalogue")
async def catalogue() -> Response:
    """Every exercise: the decks that work, and the ones that do not yet."""
    decks = await analytics.deck_shelves(get_db())
    return jsonify(
        {
            "decks": decks,
            "planned": [dict(item) for item in PLANNED_DECKS],
            "counts": {
                "available": len(decks),
                "planned": sum(1 for d in PLANNED_DECKS if d["status"] == "planned"),
                "experimental": sum(1 for d in PLANNED_DECKS if d["status"] == "experimental"),
            },
        }
    )


@api_bp.get("/games")
async def game_catalogue() -> Response:
    """The games the dashboard offers, with a live preview of each board."""
    db = get_db()
    cards = []
    for script in games.SCRIPTS:
        for card in games.game_cards(script):
            board = await games.build_board(db, mode=card["mode"], pairs=3, script=script)
            cards.append(
                {
                    **card,
                    # A couple of real characters, so the card previews the board
                    # it will actually deal rather than showing decoration.
                    "preview": [t.text for t in board.tiles if t.kind == "glyph"][:3],
                    "source": board.source,
                }
            )
    return jsonify({"games": cards})


@api_bp.post("/game/board")
async def game_board() -> Any:
    """Deal a memory board, seeded from the learner's weakest characters."""
    body = await request.get_json(silent=True) or {}
    try:
        board = await games.build_board(
            get_db(),
            mode=body.get("mode", "matchup"),
            pairs=int(body.get("pairs", games.DEFAULT_PAIRS)),
            difficulty=body.get("difficulty"),
            character_ids=body.get("character_ids") or None,
            script=body.get("script") or None,
        )
    except ValueError as exc:
        return _error("invalid_request", str(exc), 400)
    if not board.tiles:
        return _error("empty_board", "no characters available for a board", 404)
    return jsonify(board.as_dict())


@api_bp.post("/game/mispair")
async def game_mispair() -> Any:
    """Record a wrong pairing.

    Mis-pairings feed the confusion signal — an unambiguous "I think X reads as
    Y" — but deliberately NOT the drill queue or SRS: as a board empties,
    elimination makes a late match nearly free, so counting it as knowledge
    would inflate mastery.
    """
    body = await request.get_json(silent=True) or {}
    if "character_id" not in body:
        return _error("invalid_request", "character_id is required", 400)
    db = get_db()
    session_id = body.get("session_id")
    if session_id is None:
        return jsonify({"recorded": False, "reason": "no session"})
    await db.execute(
        "INSERT INTO attempts(session_id, character_id, answered_at, correct,"
        " skipped, latency_ms, first_attempt, given_answer)"
        " VALUES (?, ?, datetime('now'), 0, 0, NULL, 0, ?)",
        (int(session_id), int(body["character_id"]), body.get("given_answer")),
    )
    return jsonify({"recorded": True})


@api_bp.get("/character/<int:character_id>")
async def character_detail(character_id: int) -> Any:
    """A character plus its recall history."""
    db = get_db()
    character = await get_character(db, character_id)
    if character is None:
        return _error("not_found", f"no character {character_id}", 404)
    history = await db.fetch_all(
        "SELECT answered_at, correct, latency_ms, given_answer FROM attempts"
        " WHERE character_id = ? ORDER BY answered_at DESC LIMIT 50",
        (character_id,),
    )
    return jsonify({"character": _card(character), "history": history})


@api_bp.get("/audio/<int:character_id>")
async def character_audio(character_id: int) -> Any:
    """Pronunciation audio. Never fails — falls back to a silent clip."""
    character = await get_character(get_db(), character_id)
    if character is None:
        return _error("not_found", f"no character {character_id}", 404)
    voice = request.args.get("voice", "female")
    if voice not in ("female", "male"):
        return _error("invalid_request", f"unknown voice: {voice!r}", 400)
    payload, mimetype = await audio.get_audio(character, gender=voice)
    return Response(payload, mimetype=mimetype)

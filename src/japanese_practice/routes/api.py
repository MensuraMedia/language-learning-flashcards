"""JSON API.

Every error response is ``{"code", "message"}`` with an appropriate status.
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any

from quart import Blueprint, Response, current_app, jsonify, request

from .. import analytics, audio, games, tts_voicevox
from .. import session as session_engine
from ..db import Database, available_segments, get_character

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


def _card(character: Any, choices: list[str] | None = None) -> dict[str, Any]:
    """A character as the study view needs it — front and back separated."""
    return {
        "choices": choices or [],
        "answer": session_engine.answer_text(character),
        "id": character.id,
        "glyph": character.glyph,
        "script": character.script,
        "romaji": character.romaji,
        "meaning": character.meaning,
        "onyomi": character.onyomi,
        "kunyomi": character.kunyomi,
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
        payload.append(_card(card, await session_engine.build_choices(db, card)))

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


@api_bp.get("/games")
async def game_catalogue() -> Response:
    """The games the dashboard offers, with a live preview of each board."""
    db = get_db()
    cards = []
    for card in games.GAME_CARDS:
        board = await games.build_board(db, mode=card["mode"], pairs=3)
        cards.append(
            {
                **card,
                # A couple of real characters, so the card previews the board it
                # will actually deal rather than showing decoration.
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
            difficulty=body.get("difficulty", "hiragana:gojuon"),
            character_ids=body.get("character_ids") or None,
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

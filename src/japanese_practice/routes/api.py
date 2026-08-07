"""JSON API.

Every error response is ``{"code", "message"}`` with an appropriate status.
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any

from quart import Blueprint, Response, current_app, jsonify, request

from .. import analytics, audio
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


def _card(character: Any) -> dict[str, Any]:
    """A character as the study view needs it — front and back separated."""
    return {
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

    return jsonify(
        {
            "session_id": record.id,
            "challenge": challenge,
            "scoring": scoring,
            "difficulty": difficulty,
            "cards": [_card(c) for c in cards],
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
    payload, mimetype = await audio.get_audio(character)
    return Response(payload, mimetype=mimetype)

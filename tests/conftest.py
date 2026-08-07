"""Shared fixtures.

Every test runs against a throwaway SQLite file, never the user's real database.
`JP_DB_PATH` and `JP_AUDIO_CACHE_DIR` are redirected per test so nothing in the
suite can touch `~/.local/share/japanese-practice/`.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio

from japanese_practice.config import Config
from japanese_practice.db import Database
from japanese_practice.models import CharacterSeed


@pytest.fixture
def config(tmp_path) -> Config:
    """Config pointed entirely at a temporary directory."""
    return Config(
        db_path=tmp_path / "test.db",
        audio_cache_dir=tmp_path / "audio-cache",
    )


@pytest_asyncio.fixture
async def db(config: Config):
    """An initialised, empty database. Schema applied, no content seeded."""
    database = Database(config.db_path)
    await database.connect()
    await database.init_schema()
    yield database
    await database.close()


@pytest_asyncio.fixture
async def seeded_db(db: Database):
    """A database with a handful of known characters.

    Deliberately small and hand-written so tests can assert exact numbers
    rather than depending on the full 315-character content modules.
    """
    seeds = [
        CharacterSeed(glyph="あ", script="hiragana", romaji="a", kana_group="gojuon"),
        CharacterSeed(glyph="し", script="hiragana", romaji="shi", kana_group="gojuon"),
        CharacterSeed(glyph="つ", script="hiragana", romaji="tsu", kana_group="gojuon"),
        CharacterSeed(glyph="が", script="hiragana", romaji="ga", kana_group="dakuon"),
        CharacterSeed(glyph="ア", script="katakana", romaji="a", kana_group="gojuon"),
        CharacterSeed(
            glyph="水",
            script="kanji",
            meaning="water",
            onyomi="スイ",
            kunyomi="みず",
            jlpt_level="N5",
        ),
    ]
    await db.execute_many(
        "INSERT INTO characters"
        "(glyph, script, romaji, meaning, onyomi, kunyomi, kana_group, jlpt_level,"
        " category, stroke_count)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                s.glyph,
                s.script,
                s.romaji,
                s.meaning,
                s.onyomi,
                s.kunyomi,
                s.kana_group,
                s.jlpt_level,
                s.category,
                s.stroke_count,
            )
            for s in seeds
        ],
    )
    return db


@pytest.fixture
def iso():
    """Build an ISO-8601 UTC timestamp `days` ago, for deterministic history."""

    def _iso(days_ago: float = 0, hour: int | None = None) -> str:
        moment = datetime.now(timezone.utc) - timedelta(days=days_ago)
        if hour is not None:
            moment = moment.replace(hour=hour, minute=0, second=0, microsecond=0)
        return moment.isoformat(timespec="seconds")

    return _iso


@pytest_asyncio.fixture
async def app(config: Config, monkeypatch):
    """A Quart app wired to the temporary database."""
    monkeypatch.setenv("JP_DB_PATH", str(config.db_path))
    monkeypatch.setenv("JP_AUDIO_CACHE_DIR", str(config.audio_cache_dir))
    from japanese_practice.app import create_app

    application = create_app(config)
    application.config["TESTING"] = True
    return application

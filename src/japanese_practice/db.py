"""aiosqlite access layer.

Everything that touches SQLite goes through :class:`Database`. Rows are handed
back as plain ``dict`` objects so that route handlers and the analytics module
can serialise them straight to JSON.

All SQL is parameterised — no value is ever formatted into a statement.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Any

import aiosqlite

from .config import Config
from .models import Character

if TYPE_CHECKING:  # pragma: no cover - typing-only, never imported at runtime
    from typing_extensions import Self  # Python < 3.11 stand-in for typing.Self

__all__ = [
    "DIFFICULTY_KEYS",
    "JLPT_LEVELS",
    "KANA_GROUPS",
    "KANJI_VOLUME_TIERS",
    "SCHEMA_PATH",
    "SCRIPTS",
    "Database",
    "available_segments",
    "characters_for_difficulty",
    "connect",
    "count_for_difficulty",
    "difficulty_label",
    "get_character",
    "get_character_by_glyph",
    "list_characters",
    "parse_difficulty",
]

SCHEMA_PATH = Path(__file__).with_name("schema.sql")

SCRIPTS: tuple[str, ...] = ("hiragana", "katakana", "kanji")
KANA_GROUPS: tuple[str, ...] = ("gojuon", "dakuon", "handakuon", "yoon")
JLPT_LEVELS: tuple[str, ...] = ("N5", "N4", "N3", "N2", "N1")
KANJI_VOLUME_TIERS: dict[str, int] = {"top200": 200, "top500": 500}

#: The complete set of valid difficulty keys (BUILD-SPEC section 5).
DIFFICULTY_KEYS: tuple[str, ...] = (
    "hiragana:gojuon",
    "hiragana:dakuon",
    "hiragana:handakuon",
    "hiragana:yoon",
    "hiragana:all",
    "katakana:gojuon",
    "katakana:dakuon",
    "katakana:handakuon",
    "katakana:yoon",
    "katakana:all",
    "kanji:N5",
    "kanji:N4",
    "kanji:N3",
    "kanji:N2",
    "kanji:N1",
    "kanji:top200",
    "kanji:top500",
)

_GROUP_LABELS: dict[str, str] = {
    "gojuon": "Gojuon",
    "dakuon": "Dakuon",
    "handakuon": "Han-dakuon",
    "yoon": "Yoon",
    "all": "All",
    "top200": "Top 200",
    "top500": "Top 500",
}

_SCRIPT_LABELS: dict[str, str] = {
    "hiragana": "Hiragana",
    "katakana": "Katakana",
    "kanji": "Kanji",
}

_CHARACTER_COLUMNS = (
    "id, glyph, script, romaji, meaning, onyomi, kunyomi, "
    "kana_group, jlpt_level, category, stroke_count"
)
_SELECT_CHARACTER = f"SELECT {_CHARACTER_COLUMNS} FROM characters"


class Database:
    """An open aiosqlite connection with dict-row helpers.

    Use :func:`connect` for the normal path; instantiate directly only when you
    want to control connection and schema initialisation separately.
    """

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self._conn: aiosqlite.Connection | None = None
        self._write_lock = asyncio.Lock()

    # -- lifecycle ---------------------------------------------------------

    @property
    def connection(self) -> aiosqlite.Connection:
        """The live connection, raising if :meth:`connect` has not run."""
        if self._conn is None:
            raise RuntimeError("Database is not connected; await connect() first")
        return self._conn

    @property
    def is_connected(self) -> bool:
        """Whether a connection is currently open."""
        return self._conn is not None

    async def connect(self) -> Database:
        """Open the connection and enable WAL plus foreign-key enforcement."""
        if self._conn is not None:
            return self
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = await aiosqlite.connect(self.path)
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA foreign_keys=ON")
        await conn.execute("PRAGMA synchronous=NORMAL")
        await conn.commit()
        self._conn = conn
        return self

    async def init_schema(self) -> Database:
        """Execute ``schema.sql``. Idempotent — the DDL is all ``IF NOT EXISTS``."""
        ddl = SCHEMA_PATH.read_text(encoding="utf-8")
        async with self._write_lock:
            await self.connection.executescript(ddl)
            await self.connection.commit()
        return self

    async def close(self) -> None:
        """Close the connection if it is open."""
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    async def __aenter__(self) -> Self:
        await self.connect()
        await self.init_schema()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.close()

    # -- generic helpers ---------------------------------------------------

    async def fetch_all(
        self, sql: str, params: Sequence[Any] | Mapping[str, Any] = ()
    ) -> list[dict[str, Any]]:
        """Run a query and return every row as a ``dict``."""
        async with self.connection.execute(sql, params) as cursor:
            rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def fetch_one(
        self, sql: str, params: Sequence[Any] | Mapping[str, Any] = ()
    ) -> dict[str, Any] | None:
        """Run a query and return the first row as a ``dict``, or ``None``."""
        async with self.connection.execute(sql, params) as cursor:
            row = await cursor.fetchone()
        return dict(row) if row is not None else None

    async def fetch_value(
        self,
        sql: str,
        params: Sequence[Any] | Mapping[str, Any] = (),
        default: Any = None,
    ) -> Any:
        """Run a query and return the first column of the first row."""
        async with self.connection.execute(sql, params) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return default
        value = row[0]
        return default if value is None else value

    async def execute(
        self, sql: str, params: Sequence[Any] | Mapping[str, Any] = ()
    ) -> int:
        """Run a write statement, commit, and return ``lastrowid``."""
        async with self._write_lock:
            async with self.connection.execute(sql, params) as cursor:
                last_id = cursor.lastrowid
            await self.connection.commit()
        return int(last_id or 0)

    async def execute_many(
        self, sql: str, params_seq: Iterable[Sequence[Any] | Mapping[str, Any]]
    ) -> int:
        """Run a write statement over many parameter sets; return the row count."""
        rows = list(params_seq)
        if not rows:
            return 0
        async with self._write_lock:
            async with self.connection.executemany(sql, rows) as cursor:
                count = cursor.rowcount
            await self.connection.commit()
        return int(count if count and count > 0 else len(rows))

    async def execute_script(self, sql: str) -> None:
        """Run a multi-statement script and commit."""
        async with self._write_lock:
            await self.connection.executescript(sql)
            await self.connection.commit()


async def connect(config: Config | None = None) -> Database:
    """Open the configured database, enable pragmas and apply the schema."""
    cfg = config if config is not None else Config.from_env()
    db = Database(cfg.db_path)
    await db.connect()
    await db.init_schema()
    return db


# -- difficulty keys -------------------------------------------------------


def parse_difficulty(difficulty: str) -> tuple[str, str]:
    """Split a difficulty key into ``(script, group)``.

    Raises ``ValueError`` for anything outside :data:`DIFFICULTY_KEYS`.
    """
    if difficulty not in DIFFICULTY_KEYS:
        raise ValueError(f"unknown difficulty key: {difficulty!r}")
    script, _, group = difficulty.partition(":")
    return script, group


def difficulty_label(difficulty: str) -> str:
    """A human-readable name for a difficulty key, e.g. ``Hiragana · Gojuon``."""
    script, group = parse_difficulty(difficulty)
    return f"{_SCRIPT_LABELS[script]} · {_GROUP_LABELS.get(group, group)}"


def _difficulty_clause(difficulty: str) -> tuple[str, list[Any], int | None]:
    """Return ``(where_sql, params, limit)`` for a difficulty key."""
    script, group = parse_difficulty(difficulty)
    if group == "all":
        return "script = ?", [script], None
    if script == "kanji":
        if group in KANJI_VOLUME_TIERS:
            return "script = ?", [script], KANJI_VOLUME_TIERS[group]
        return "script = ? AND jlpt_level = ?", [script, group], None
    return "script = ? AND kana_group = ?", [script, group], None


async def characters_for_difficulty(db: Database, difficulty: str) -> list[Character]:
    """Every character belonging to a difficulty key, in seed (frequency) order.

    ``hiragana:all`` and ``katakana:all`` return the whole script. The kanji
    volume tiers (``kanji:top200`` / ``kanji:top500``) take the first N kanji in
    seed order, which the content modules keep in frequency order.
    """
    where, params, limit = _difficulty_clause(difficulty)
    sql = f"{_SELECT_CHARACTER} WHERE {where} ORDER BY id"
    if limit is not None:
        sql += " LIMIT ?"
        params = [*params, limit]
    rows = await db.fetch_all(sql, params)
    return [Character.from_row(row) for row in rows]


async def count_for_difficulty(db: Database, difficulty: str) -> int:
    """How many characters a difficulty key currently resolves to."""
    where, params, limit = _difficulty_clause(difficulty)
    total = int(
        await db.fetch_value(
            f"SELECT COUNT(*) FROM characters WHERE {where}", params, default=0
        )
    )
    return min(total, limit) if limit is not None else total


async def list_characters(db: Database, script: str | None = None) -> list[Character]:
    """All characters, optionally restricted to one script."""
    if script is None:
        rows = await db.fetch_all(f"{_SELECT_CHARACTER} ORDER BY id")
    else:
        rows = await db.fetch_all(
            f"{_SELECT_CHARACTER} WHERE script = ? ORDER BY id", [script]
        )
    return [Character.from_row(row) for row in rows]


async def get_character(db: Database, character_id: int) -> Character | None:
    """Look a character up by primary key."""
    row = await db.fetch_one(f"{_SELECT_CHARACTER} WHERE id = ?", [character_id])
    return Character.from_row(row) if row is not None else None


async def get_character_by_glyph(db: Database, glyph: str) -> Character | None:
    """Look a character up by its glyph, which is unique."""
    row = await db.fetch_one(f"{_SELECT_CHARACTER} WHERE glyph = ?", [glyph])
    return Character.from_row(row) if row is not None else None


async def available_segments(db: Database) -> list[dict[str, Any]]:
    """The difficulty keys that currently have at least one seeded character.

    Shape: ``[{key, script, group, label, count}]`` — ready for ``/api/segments``.
    """
    segments: list[dict[str, Any]] = []
    for key in DIFFICULTY_KEYS:
        count = await count_for_difficulty(db, key)
        if count == 0:
            continue
        script, group = parse_difficulty(key)
        segments.append(
            {
                "key": key,
                "script": script,
                "group": group,
                "label": difficulty_label(key),
                "count": count,
            }
        )
    return segments

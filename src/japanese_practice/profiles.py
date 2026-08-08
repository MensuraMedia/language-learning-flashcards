"""Study profiles: one learner's history, kept in its own database file.

**Why a file per profile rather than a column.** Every analytics query in this
project reads the `attempts` table directly. Adding a `profile_id` would mean
threading a filter through all of them, and one forgotten `WHERE` would silently
mix two people's histories — the failure would look like bad data rather than a
bug. A file cannot be half-filtered: the connection is either open on your
profile or it is not. It also makes the two operations users actually ask for
trivial and safe. Exporting is copying a file. Deleting a profile is deleting
one, with no rows left behind pointing at it.

The cost is that switching profiles reopens the connection, which is why
:func:`activate` is the only way to do it.

The default profile keeps using the configured `db_path`, so an existing install
becomes "Default" with its history intact and nothing to migrate.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import Config

__all__ = [
    "DEFAULT_SLUG",
    "Profile",
    "activate",
    "active_slug",
    "create",
    "delete",
    "list_profiles",
    "path_for",
    "slugify",
]

DEFAULT_SLUG = "default"
DEFAULT_NAME = "Default"

#: Slugs are used as filenames, so the character set is deliberately narrow.
_SAFE = re.compile(r"[^a-z0-9]+")
MAX_NAME_LENGTH = 40


def slugify(name: str) -> str:
    """A filename-safe slug. Raises ``ValueError`` if nothing usable is left.

    Non-ASCII names are common here — a profile called ひろ is entirely
    reasonable — and they reduce to an empty slug, so those fall back to a hash
    of the name rather than being rejected.
    """
    folded = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    slug = _SAFE.sub("-", folded.lower()).strip("-")
    if not slug:
        slug = "p" + format(abs(hash(name.strip())) % 0xFFFFFF, "06x")
    return slug[:48]


@dataclass(frozen=True)
class Profile:
    """One profile and the state of its database file."""

    slug: str
    name: str
    path: Path
    active: bool
    exists: bool
    size_bytes: int
    modified_at: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "name": self.name,
            "active": self.active,
            "exists": self.exists,
            "size_bytes": self.size_bytes,
            "modified_at": self.modified_at,
        }


def _root(config: Config) -> Path:
    return config.db_path.parent


def _index_path(config: Config) -> Path:
    """Display names, which the filesystem cannot hold faithfully."""
    return _root(config) / "profiles.json"


def _active_path(config: Config) -> Path:
    return _root(config) / "active-profile"


def path_for(config: Config, slug: str) -> Path:
    """Where a profile's database lives."""
    if slug == DEFAULT_SLUG:
        return config.db_path
    return _root(config) / "profiles" / f"{slug}.db"


def _read_index(config: Config) -> dict[str, str]:
    try:
        data = json.loads(_index_path(config).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {str(k): str(v) for k, v in data.items()} if isinstance(data, dict) else {}


def _write_index(config: Config, index: dict[str, str]) -> None:
    path = _index_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")


def active_slug(config: Config) -> str:
    """The slug currently in use, defaulting to the built-in profile."""
    try:
        slug = _active_path(config).read_text(encoding="utf-8").strip()
    except OSError:
        return DEFAULT_SLUG
    return slug or DEFAULT_SLUG


def _set_active_slug(config: Config, slug: str) -> None:
    path = _active_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(slug, encoding="utf-8")


def list_profiles(config: Config) -> list[Profile]:
    """Every known profile, the default first and the rest by name."""
    index = _read_index(config)
    index.setdefault(DEFAULT_SLUG, DEFAULT_NAME)
    active = active_slug(config)

    out: list[Profile] = []
    for slug, name in index.items():
        path = path_for(config, slug)
        stat = path.stat() if path.exists() else None
        out.append(
            Profile(
                slug=slug,
                name=name,
                path=path,
                active=slug == active,
                exists=stat is not None,
                size_bytes=stat.st_size if stat else 0,
                modified_at=(
                    datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
                    if stat
                    else None
                ),
            )
        )
    out.sort(key=lambda p: (p.slug != DEFAULT_SLUG, p.name.lower()))
    return out


def create(config: Config, name: str) -> Profile:
    """Register a profile. Its database is created when it is first activated."""
    clean = " ".join(name.split())[:MAX_NAME_LENGTH]
    if not clean:
        raise ValueError("a profile needs a name")

    slug = slugify(clean)
    index = _read_index(config)
    index.setdefault(DEFAULT_SLUG, DEFAULT_NAME)
    if slug in index:
        raise ValueError(f"a profile named {index[slug]!r} already exists")
    index[slug] = clean
    _write_index(config, index)
    return next(p for p in list_profiles(config) if p.slug == slug)


def delete(config: Config, slug: str) -> None:
    """Forget a profile and remove its database.

    The default profile cannot be deleted — it is the fallback the app returns
    to, and removing it would leave no profile to activate. Nor can the active
    one, because the connection is open on it.
    """
    if slug == DEFAULT_SLUG:
        raise ValueError("the default profile cannot be deleted")
    if slug == active_slug(config):
        raise ValueError("switch to another profile before deleting this one")

    index = _read_index(config)
    if slug not in index:
        raise ValueError(f"unknown profile: {slug!r}")
    del index[slug]
    _write_index(config, index)

    path = path_for(config, slug)
    # WAL leaves two sidecar files; deleting only the .db would resurrect the
    # profile's tail on next open.
    for suffix in ("", "-wal", "-shm"):
        candidate = path.with_name(path.name + suffix)
        candidate.unlink(missing_ok=True)


def resolve(config: Config, slug: str) -> Profile:
    """Look one up, raising ``ValueError`` if it is not registered."""
    for profile in list_profiles(config):
        if profile.slug == slug:
            return profile
    raise ValueError(f"unknown profile: {slug!r}")


def activate(config: Config, slug: str) -> Profile:
    """Mark a profile active. The caller reopens the database."""
    profile = resolve(config, slug)
    profile.path.parent.mkdir(parents=True, exist_ok=True)
    _set_active_slug(config, slug)
    return profile


def active_db_path(config: Config) -> Path:
    """The database file the app should open on start-up."""
    return path_for(config, active_slug(config))

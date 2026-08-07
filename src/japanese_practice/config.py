"""Application configuration: paths, server binding and environment overrides.

Defaults are XDG-aware and live under ``~/.local/share/japanese-practice``
(honouring ``XDG_DATA_HOME`` when it is set). Every field can be overridden with
a ``JP_``-prefixed environment variable:

===================  ==========================  ==========================
Field                Environment variable        Example
===================  ==========================  ==========================
``db_path``          ``JP_DB_PATH``              ``/srv/jp/practice.db``
``audio_cache_dir``  ``JP_AUDIO_CACHE_DIR``      ``/srv/jp/audio``
``host``             ``JP_HOST``                 ``0.0.0.0``
``port``             ``JP_PORT``                 ``8765``
``debug``            ``JP_DEBUG``                ``1`` / ``true`` / ``yes``
===================  ==========================  ==========================
"""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path

__all__ = [
    "APP_DIR_NAME",
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "Config",
    "data_dir",
    "default_config",
]

APP_DIR_NAME = "japanese-practice"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765

_DB_FILENAME = "practice.db"
_AUDIO_CACHE_DIRNAME = "audio-cache"
_TRUTHY = {"1", "true", "yes", "on"}
_FALSY = {"0", "false", "no", "off", ""}


def data_dir() -> Path:
    """Return the XDG data directory for this application.

    ``$XDG_DATA_HOME/japanese-practice`` when the variable is set to an absolute
    path, otherwise ``~/.local/share/japanese-practice``.
    """
    raw = os.environ.get("XDG_DATA_HOME", "").strip()
    base = Path(raw) if raw else Path.home() / ".local" / "share"
    if not base.is_absolute():
        base = Path.home() / ".local" / "share"
    return base / APP_DIR_NAME


def _env_path(name: str, default: Path) -> Path:
    raw = os.environ.get(name, "").strip()
    return Path(raw).expanduser() if raw else default


def _env_str(name: str, default: str) -> str:
    raw = os.environ.get(name, "").strip()
    return raw or default


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if raw in _TRUTHY:
        return True
    if raw in _FALSY:
        return default if raw == "" else False
    raise ValueError(f"{name} must be a boolean-ish value, got {raw!r}")


@dataclass(frozen=True, slots=True)
class Config:
    """Runtime configuration for the app."""

    db_path: Path
    audio_cache_dir: Path
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    debug: bool = False

    @classmethod
    def default(cls) -> Config:
        """Configuration from the XDG defaults, ignoring the environment."""
        root = data_dir()
        return cls(
            db_path=root / _DB_FILENAME,
            audio_cache_dir=root / _AUDIO_CACHE_DIRNAME,
        )

    @classmethod
    def from_env(cls) -> Config:
        """Configuration from the XDG defaults with ``JP_*`` overrides applied."""
        base = cls.default()
        return cls(
            db_path=_env_path("JP_DB_PATH", base.db_path),
            audio_cache_dir=_env_path("JP_AUDIO_CACHE_DIR", base.audio_cache_dir),
            host=_env_str("JP_HOST", base.host),
            port=_env_int("JP_PORT", base.port),
            debug=_env_bool("JP_DEBUG", base.debug),
        )

    def with_overrides(
        self,
        *,
        db_path: Path | str | None = None,
        audio_cache_dir: Path | str | None = None,
        host: str | None = None,
        port: int | None = None,
        debug: bool | None = None,
    ) -> Config:
        """Return a copy with the given values replaced (``None`` keeps current)."""
        changes: dict[str, object] = {}
        if db_path is not None:
            changes["db_path"] = Path(db_path).expanduser()
        if audio_cache_dir is not None:
            changes["audio_cache_dir"] = Path(audio_cache_dir).expanduser()
        if host is not None:
            changes["host"] = host
        if port is not None:
            changes["port"] = int(port)
        if debug is not None:
            changes["debug"] = bool(debug)
        return replace(self, **changes)

    def ensure_dirs(self) -> Config:
        """Create the database and audio-cache directories if they are missing."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.audio_cache_dir.mkdir(parents=True, exist_ok=True)
        return self

    @property
    def base_url(self) -> str:
        """The URL the desktop shell should point its webview at."""
        return f"http://{self.host}:{self.port}"


def default_config() -> Config:
    """Convenience wrapper: :meth:`Config.from_env` with directories created."""
    return Config.from_env().ensure_dirs()

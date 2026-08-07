"""Command-line entry point: local Quart server plus the pywebview desktop shell.

Default behaviour starts the server on a background thread (with its own event
loop) and opens a native window pointed at it. ``--no-window`` skips the window
and simply serves, printing the URL. If pywebview is missing or cannot open a
window (headless box, no GTK/Qt backend), the shell degrades to server-only mode
instead of crashing.

Configuration layering, highest priority first: command-line flags, ``JP_*``
environment variables (see :mod:`japanese_practice.config`), built-in defaults.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import os
import signal
import socket
import sys
import threading
import time
from collections.abc import Sequence
from types import FrameType
from typing import TYPE_CHECKING, Any

from . import __version__
from .config import Config

if TYPE_CHECKING:  # pragma: no cover - typing only
    from quart import Quart

__all__ = ["DEFAULT_PORT", "ServerThread", "build_parser", "main"]

DEFAULT_PORT = 8731

WINDOW_TITLE = "Japanese Practice — 日本語練習"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 860
WINDOW_MIN_SIZE = (900, 640)

STARTUP_TIMEOUT = 20.0
SHUTDOWN_TIMEOUT = 10.0

_LOOPBACK_FOR = {"0.0.0.0": "127.0.0.1", "::": "::1", "": "127.0.0.1"}


def _warn(message: str) -> None:
    print(f"japanese-practice: {message}", file=sys.stderr)


class ServerThread:
    """Run a Quart app on a dedicated event loop in a background thread.

    The loop is private to the thread, so nothing else may schedule work on it
    directly; :meth:`stop` hands the shutdown signal over with
    ``call_soon_threadsafe``.
    """

    def __init__(self, app: Quart, config: Config) -> None:
        self._app = app
        self._config = config
        self._thread = threading.Thread(
            target=self._run, name="japanese-practice-server", daemon=True
        )
        self._loop: asyncio.AbstractEventLoop | None = None
        self._stop: asyncio.Event | None = None
        self._loop_ready = threading.Event()
        self._error: BaseException | None = None

    # -- lifecycle ---------------------------------------------------------

    def start(self) -> None:
        """Start the background thread and wait until its loop exists."""
        self._thread.start()
        self._loop_ready.wait(STARTUP_TIMEOUT)

    def wait_until_ready(self, timeout: float = STARTUP_TIMEOUT) -> None:
        """Block until the server accepts connections.

        Raises ``RuntimeError`` if the server thread died during startup and
        ``TimeoutError`` if it never began listening.
        """
        host = _LOOPBACK_FOR.get(self._config.host, self._config.host)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._error is not None:
                raise RuntimeError(f"server failed to start: {self._error}") from self._error
            if not self._thread.is_alive():
                raise RuntimeError("server thread exited before it began listening")
            try:
                with socket.create_connection((host, self._config.port), timeout=0.5):
                    return
            except OSError:
                time.sleep(0.05)
        raise TimeoutError(f"server did not start listening within {timeout:.0f}s")

    def stop(self, timeout: float = SHUTDOWN_TIMEOUT) -> None:
        """Ask the server to shut down and wait for the thread to finish."""
        loop, stop = self._loop, self._stop
        if loop is not None and stop is not None and not loop.is_closed():
            # The loop can close between the check and the call.
            with contextlib.suppress(RuntimeError):
                loop.call_soon_threadsafe(stop.set)
        self._thread.join(timeout)

    def is_alive(self) -> bool:
        """True while the server thread is still running."""
        return self._thread.is_alive()

    @property
    def error(self) -> BaseException | None:
        """The exception that killed the server thread, if any."""
        return self._error

    # -- thread body -------------------------------------------------------

    def _run(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        self._stop = asyncio.Event()
        self._loop_ready.set()
        try:
            loop.run_until_complete(
                self._app.run_task(
                    host=self._config.host,
                    port=self._config.port,
                    debug=self._config.debug,
                    shutdown_trigger=self._stop.wait,
                )
            )
        except BaseException as exc:  # noqa: BLE001 - reported to the main thread
            self._error = exc
        finally:
            try:
                _drain_loop(loop)
            finally:
                asyncio.set_event_loop(None)
                loop.close()


def _drain_loop(loop: asyncio.AbstractEventLoop) -> None:
    """Cancel outstanding tasks and close async generators before closing."""
    pending = [task for task in asyncio.all_tasks(loop) if not task.done()]
    for task in pending:
        task.cancel()
    if pending:
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    loop.run_until_complete(loop.shutdown_asyncgens())


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="japanese-practice",
        description="Flash-card practice for kana and kanji, served locally.",
    )
    parser.add_argument(
        "--no-window",
        action="store_true",
        help="serve only; do not open the desktop window",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        metavar="PORT",
        help=f"port to listen on (default: {DEFAULT_PORT}, or $JP_PORT)",
    )
    parser.add_argument(
        "--host",
        default=None,
        metavar="HOST",
        help="interface to bind (default: 127.0.0.1, or $JP_HOST)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="enable Quart debug mode and auto-reload-friendly errors",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def resolve_config(args: argparse.Namespace) -> Config:
    """Fold the CLI flags over the environment-derived configuration."""
    config = Config.from_env()
    if args.port is None and not os.environ.get("JP_PORT", "").strip():
        config = config.with_overrides(port=DEFAULT_PORT)
    return config.with_overrides(
        host=args.host,
        port=args.port,
        debug=True if args.debug else None,
    ).ensure_dirs()


def _export_config(config: Config) -> None:
    """Publish the resolved settings so ``create_app()`` reads the same values.

    ``create_app()`` takes no arguments, and :class:`Config` is built from the
    ``JP_*`` environment; writing the resolved values back is how CLI flags
    reach the application.
    """
    os.environ["JP_DB_PATH"] = str(config.db_path)
    os.environ["JP_AUDIO_CACHE_DIR"] = str(config.audio_cache_dir)
    os.environ["JP_HOST"] = config.host
    os.environ["JP_PORT"] = str(config.port)
    os.environ["JP_DEBUG"] = "1" if config.debug else "0"


def _import_webview() -> Any | None:
    """Import pywebview, or return ``None`` if it is unavailable."""
    try:
        import webview
    except ImportError:
        _warn("pywebview is not installed; falling back to server-only mode.")
        _warn("Install it with: pip install pywebview")
        return None
    except Exception as exc:  # noqa: BLE001 - a broken GUI stack must not be fatal
        _warn(f"pywebview could not be loaded ({exc}); falling back to server-only mode.")
        return None
    return webview


def _open_window(webview: Any, url: str) -> None:
    """Open the desktop window and block until the user closes it."""
    webview.create_window(
        WINDOW_TITLE,
        url,
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        resizable=True,
        min_size=WINDOW_MIN_SIZE,
    )
    webview.start()


def _serve_until_signal(server: ServerThread, url: str) -> int:
    """Serve until SIGINT/SIGTERM, or until the server thread dies."""
    stop = threading.Event()

    def _handle(signum: int, frame: FrameType | None) -> None:
        stop.set()

    installed: dict[int, Any] = {}
    for sig in (signal.SIGINT, signal.SIGTERM):
        # Not the main thread, or no such signal on this platform.
        with contextlib.suppress(OSError, ValueError, AttributeError):
            installed[sig] = signal.signal(sig, _handle)

    print(f"Japanese Practice is serving at {url}")
    print("Press Ctrl+C to stop.")
    try:
        while not stop.is_set() and server.is_alive():
            stop.wait(0.25)
    except KeyboardInterrupt:
        pass
    finally:
        for sig, previous in installed.items():
            with contextlib.suppress(OSError, ValueError):
                signal.signal(sig, previous)

    error = server.error
    server.stop()
    if error is not None:
        _warn(f"server stopped with an error: {error}")
        return 1
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the application. Returns the process exit code."""
    args = build_parser().parse_args(argv)
    config = resolve_config(args)
    _export_config(config)

    from .app import create_app

    app = create_app()
    server = ServerThread(app, config)
    server.start()
    try:
        server.wait_until_ready()
    except (RuntimeError, TimeoutError) as exc:
        _warn(str(exc))
        server.stop()
        return 1

    url = config.base_url
    if args.no_window:
        return _serve_until_signal(server, url)

    webview = _import_webview()
    if webview is None:
        return _serve_until_signal(server, url)

    print(f"Japanese Practice is serving at {url}")
    try:
        _open_window(webview, url)
    except KeyboardInterrupt:
        pass
    except Exception as exc:  # noqa: BLE001 - no display, no backend, etc.
        _warn(f"could not open a desktop window ({exc}); serving without one.")
        return _serve_until_signal(server, url)

    server.stop()
    error = server.error
    if error is not None:
        _warn(f"server stopped with an error: {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Server-rendered HTML views."""

from __future__ import annotations

from quart import Blueprint, render_template

views_bp = Blueprint("views", __name__)


@views_bp.get("/")
async def dashboard() -> str:
    """The landing page: deck shelf plus the full analytics surface."""
    return await render_template("dashboard.html")


@views_bp.get("/decks")
async def decks() -> str:
    """Every exercise in one place — what exists, and what is being built."""
    return await render_template("decks.html")


@views_bp.get("/games")
async def games_view() -> str:
    """Memory-training boards: Match Up, Pelmanism, Confusion Drill."""
    return await render_template("games.html")


@views_bp.get("/study")
async def study() -> str:
    """The flash-card view. Session parameters arrive as query args."""
    return await render_template("study.html")

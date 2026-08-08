"""Quart application factory."""

from __future__ import annotations

import logging
from pathlib import Path

from quart import Quart

from . import audio, profiles
from .config import Config, default_config
from .content.loader import seed_content
from .db import Database
from .routes.api import api_bp
from .routes.views import views_bp

log = logging.getLogger(__name__)


def create_app(config: Config | None = None) -> Quart:
    """Build the application, wire the database lifecycle, register blueprints."""
    config = (config or default_config()).ensure_dirs()

    app = Quart(__name__, static_folder="static", template_folder="templates")
    app.config["JP_CONFIG"] = config
    audio.configure(config)

    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp)

    @app.context_processor
    def _asset_version() -> dict[str, str]:
        """Cache-busting stamp for static assets.

        Embedded webviews cache aggressively — without this, a user who updates
        the app keeps the old CSS and JS until they clear the webview's cache,
        which they have no UI to do.
        """
        newest = 0.0
        static_root = Path(app.static_folder or "")
        for asset in static_root.rglob("*"):
            if asset.is_file():
                newest = max(newest, asset.stat().st_mtime)
        return {"asset_version": str(int(newest))}

    @app.before_serving
    async def _startup() -> None:
        await open_profile_db(app, profiles.active_slug(config))

    async def open_profile_db(target: Quart, slug: str) -> None:
        """Open (or reopen) the database on one profile.

        Reopening is how a profile switch works — see :mod:`.profiles` for why a
        file per profile beats a column. The old connection is closed first so
        the previous profile's WAL is checkpointed before anything reads it.
        """
        old: Database | None = target.config.get("JP_DB")
        if old is not None:
            await old.close()

        profile = profiles.activate(config, slug)
        db = Database(profile.path)
        await db.connect()
        await db.init_schema()
        seeded = await seed_content(db)
        target.config["JP_DB"] = db
        target.config["JP_PROFILE"] = profile.slug
        log.info("profile %r ready at %s (%s characters)", profile.slug, profile.path, seeded)

    # Exposed so the settings endpoints can switch profiles without importing
    # the factory, which would be circular.
    app.config["JP_OPEN_PROFILE"] = open_profile_db

    @app.after_serving
    async def _shutdown() -> None:
        db: Database | None = app.config.get("JP_DB")
        if db is not None:
            await db.close()

    return app


# ``get_db`` lives in routes.api — defining it here as well would invite the
# circular import this module already has to avoid.

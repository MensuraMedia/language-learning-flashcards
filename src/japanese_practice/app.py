"""Quart application factory."""

from __future__ import annotations

import logging

from quart import Quart

from . import audio
from .config import Config, default_config
from .content.loader import seed_content
from .db import Database, connect
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

    @app.before_serving
    async def _startup() -> None:
        db = await connect(config)
        await db.init_schema()
        seeded = await seed_content(db)
        app.config["JP_DB"] = db
        log.info("database ready at %s (%s characters)", config.db_path, seeded)

    @app.after_serving
    async def _shutdown() -> None:
        db: Database | None = app.config.get("JP_DB")
        if db is not None:
            await db.close()

    return app


# ``get_db`` lives in routes.api — defining it here as well would invite the
# circular import this module already has to avoid.

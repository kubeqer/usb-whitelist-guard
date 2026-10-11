from alembic import context
from sqlalchemy import Connection
from usb_whitelist_guard_core.storage.engine import make_engine
from usb_whitelist_guard_core.storage.models import Base


def _run(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=Base.metadata,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def _run_online() -> None:
    connection = context.config.attributes.get("connection")
    if connection is not None:
        _run(connection)
        return

    engine = make_engine(context.config.get_main_option("sqlalchemy.url"))
    try:
        with engine.connect() as connection:
            _run(connection)
    finally:
        engine.dispose()


if context.is_offline_mode():
    raise RuntimeError("Offline migrations are not supported")

_run_online()

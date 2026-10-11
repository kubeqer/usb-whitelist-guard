import argparse
import logging
from pathlib import Path

from usb_whitelist_guard_core.config import database_url, default_database_path
from usb_whitelist_guard_core.policy import AllowlistPolicy, FailSecurePolicy
from usb_whitelist_guard_core.services import GuardService
from usb_whitelist_guard_core.storage import (
    SqlAllowlistRepository,
    SqlEventRepository,
    make_engine,
    make_session_factory,
    upgrade_schema,
)

from usb_whitelist_guard_monitor.platforms import create_platform_adapters
from usb_whitelist_guard_monitor.privileges import is_privileged

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if not is_privileged():
        logger.error("The monitor must run as root / administrator")
        return 1

    engine = make_engine(database_url(args.database))
    try:
        args.database.parent.mkdir(parents=True, exist_ok=True)
        upgrade_schema(engine)
    except Exception:
        logger.exception(
            "Database %s is unavailable; every device will be blocked", args.database
        )
    sessions = make_session_factory(engine)

    watcher, blocker = create_platform_adapters()
    policy = FailSecurePolicy(AllowlistPolicy(SqlAllowlistRepository(sessions)))
    service = GuardService(watcher, policy, blocker, SqlEventRepository(sessions))

    logger.info("Watching for USB devices (database: %s)", args.database)
    try:
        service.run()
    except KeyboardInterrupt:
        logger.info("Stopped")
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="usb-whitelist-guard-monitor")
    parser.add_argument("--database", type=Path, default=default_database_path())
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args(argv)

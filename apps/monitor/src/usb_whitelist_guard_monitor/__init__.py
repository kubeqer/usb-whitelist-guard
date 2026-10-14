import argparse
import logging
from pathlib import Path

from usb_whitelist_guard_core.config import database_url, default_database_path
from usb_whitelist_guard_core.policy import AllowlistPolicy, FailSecurePolicy
from usb_whitelist_guard_core.ports import (
    AllowlistReader,
    AllowlistWriter,
    DeviceWatcher,
    EventReader,
)
from usb_whitelist_guard_core.services import (
    GuardService,
    allow_connected_devices,
    is_first_run,
)
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

    allowlist = SqlAllowlistRepository(sessions)
    events = SqlEventRepository(sessions)
    watcher, blocker = create_platform_adapters()
    _allow_connected_on_first_run(watcher, allowlist, allowlist, events)

    policy = FailSecurePolicy(AllowlistPolicy(allowlist))
    service = GuardService(watcher, policy, blocker, events)

    logger.info("Watching for USB devices (database: %s)", args.database)
    try:
        service.run()
    except KeyboardInterrupt:
        logger.info("Stopped")
    return 0


def _allow_connected_on_first_run(
    watcher: DeviceWatcher,
    reader: AllowlistReader,
    writer: AllowlistWriter,
    events: EventReader,
) -> None:
    try:
        if not is_first_run(reader, events):
            return
        logger.info("First run: allowing every USB device connected now")
        added = allow_connected_devices(watcher.connected(), writer)
    except Exception:
        logger.exception("Could not allow connected devices on first run")
        return
    logger.info("First run: %d device(s) added to the allowlist", len(added))


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="usb-whitelist-guard-monitor")
    parser.add_argument("--database", type=Path, default=default_database_path())
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args(argv)

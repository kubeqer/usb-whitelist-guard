from collections.abc import Sequence
from typing import cast

from sqlalchemy import CursorResult, Select, delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from usb_whitelist_guard_core.domain import (
    AllowlistEntry,
    AllowlistUnavailableError,
    DeviceId,
    DuplicateEntryError,
    EntryNotFoundError,
)
from usb_whitelist_guard_core.storage.mappers import entry_from_row, entry_to_row
from usb_whitelist_guard_core.storage.models import AllowlistRow


class SqlAllowlistRepository:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def candidates_for(self, vid: str, pid: str) -> Sequence[AllowlistEntry]:
        stmt = select(AllowlistRow).where(
            AllowlistRow.vid == vid, AllowlistRow.pid == pid
        )
        return self._fetch(stmt)

    def list_all(self) -> Sequence[AllowlistEntry]:
        stmt = select(AllowlistRow).order_by(
            AllowlistRow.vid, AllowlistRow.pid, AllowlistRow.serial
        )
        return self._fetch(stmt)

    def add(self, entry: AllowlistEntry) -> None:
        try:
            with self._sessions.begin() as session:
                if session.scalar(select(_matching_exactly(entry.device_id).exists())):
                    raise DuplicateEntryError(
                        f"{entry.device_id} is already on the allowlist"
                    )
                session.add(entry_to_row(entry))
        except SQLAlchemyError as exc:
            raise AllowlistUnavailableError(str(exc)) from exc

    def remove(self, device_id: DeviceId) -> None:
        try:
            with self._sessions.begin() as session:
                stmt = delete(AllowlistRow).where(*_exact_conditions(device_id))
                result = cast(CursorResult, session.execute(stmt))
                if result.rowcount == 0:
                    raise EntryNotFoundError(f"{device_id} is not on the allowlist")
        except SQLAlchemyError as exc:
            raise AllowlistUnavailableError(str(exc)) from exc

    def _fetch(self, stmt: Select[AllowlistRow]) -> list[AllowlistEntry]:
        try:
            with self._sessions() as session:
                return [entry_from_row(row) for row in session.scalars(stmt)]
        except SQLAlchemyError as exc:
            raise AllowlistUnavailableError(str(exc)) from exc


def _exact_conditions(device_id: DeviceId) -> tuple:
    serial = (
        AllowlistRow.serial.is_(None)
        if device_id.serial is None
        else AllowlistRow.serial == device_id.serial
    )
    return AllowlistRow.vid == device_id.vid, AllowlistRow.pid == device_id.pid, serial


def _matching_exactly(device_id: DeviceId) -> Select[AllowlistRow]:
    return select(AllowlistRow).where(*_exact_conditions(device_id))

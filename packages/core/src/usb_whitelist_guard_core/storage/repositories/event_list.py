from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from usb_whitelist_guard_core.domain import DeviceEvent, EventStoreError
from usb_whitelist_guard_core.storage.mappers import event_from_row, event_to_row
from usb_whitelist_guard_core.storage.models import EventRow


class SqlEventRepository:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def record(self, event: DeviceEvent) -> None:
        try:
            with self._sessions.begin() as session:
                session.add(event_to_row(event))
        except SQLAlchemyError as exc:
            raise EventStoreError(str(exc)) from exc

    def recent(self, limit: int = 100) -> Sequence[DeviceEvent]:
        stmt = (
            select(EventRow)
            .order_by(EventRow.timestamp.desc(), EventRow.id.desc())
            .limit(limit)
        )
        try:
            with self._sessions() as session:
                return [event_from_row(row) for row in session.scalars(stmt)]
        except SQLAlchemyError as exc:
            raise EventStoreError(str(exc)) from exc

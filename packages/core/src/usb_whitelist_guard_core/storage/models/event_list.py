from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from usb_whitelist_guard_core.storage.models.base import Base


class EventRow(Base):
    __tablename__ = "event_list"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    vid: Mapped[str] = mapped_column(String(4))
    pid: Mapped[str] = mapped_column(String(4))
    serial: Mapped[str | None] = mapped_column(String(255))
    decision: Mapped[str] = mapped_column(String(16))
    reason: Mapped[str] = mapped_column(Text)

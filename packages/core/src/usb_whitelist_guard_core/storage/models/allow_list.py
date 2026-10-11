from datetime import datetime

from sqlalchemy import DateTime, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from usb_whitelist_guard_core.storage.models.base import Base


class AllowlistRow(Base):
    __tablename__ = "allow_list"
    __table_args__ = (
        UniqueConstraint("vid", "pid", "serial"),
        Index("ix_allow_list_vid_pid", "vid", "pid"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    vid: Mapped[str] = mapped_column(String(4))
    pid: Mapped[str] = mapped_column(String(4))
    serial: Mapped[str | None] = mapped_column(String(255))
    note: Mapped[str | None] = mapped_column(String(255))
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )

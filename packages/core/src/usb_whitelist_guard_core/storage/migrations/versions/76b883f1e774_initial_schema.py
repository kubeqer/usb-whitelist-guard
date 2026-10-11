from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "76b883f1e774"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "allow_list",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vid", sa.String(length=4), nullable=False),
        sa.Column("pid", sa.String(length=4), nullable=False),
        sa.Column("serial", sa.String(length=255), nullable=True),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_allow_list")),
        sa.UniqueConstraint(
            "vid", "pid", "serial", name=op.f("uq_allow_list_vid_pid_serial")
        ),
    )
    with op.batch_alter_table("allow_list", schema=None) as batch_op:
        batch_op.create_index("ix_allow_list_vid_pid", ["vid", "pid"], unique=False)

    op.create_table(
        "event_list",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("vid", sa.String(length=4), nullable=False),
        sa.Column("pid", sa.String(length=4), nullable=False),
        sa.Column("serial", sa.String(length=255), nullable=True),
        sa.Column("decision", sa.String(length=16), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event_list")),
    )
    with op.batch_alter_table("event_list", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_event_list_timestamp"), ["timestamp"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("event_list", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_event_list_timestamp"))

    op.drop_table("event_list")
    with op.batch_alter_table("allow_list", schema=None) as batch_op:
        batch_op.drop_index("ix_allow_list_vid_pid")

    op.drop_table("allow_list")

"""init

Revision ID: 7e57f0e42f5e
Revises:
Create Date: 2024-10-31 19:22:56.544188

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7e57f0e42f5e"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workers",
        sa.Column("library_name", sa.VARCHAR(30), nullable=False),
        sa.Column("test_name", sa.VARCHAR(30), nullable=False),
        sa.Column("start_time", sa.DATETIME, nullable=False),
        sa.Column("end_time", sa.DATETIME, nullable=False),
        sa.Column("number_requests", sa.INTEGER, nullable=False),
        sa.Column("container_id", sa.VARCHAR, nullable=False),
        sa.Column("run_id", sa.VARCHAR, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("workers")

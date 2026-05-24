"""Agregar ruta_archivo a upload_batches para reprocesar archivos

Revision ID: 004
Revises: 003
Create Date: 2025-01-01 00:03:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "upload_batches",
        sa.Column("ruta_archivo", sa.String(500), nullable=True)
    )


def downgrade() -> None:
    with op.batch_alter_table("upload_batches") as batch_op:
        batch_op.drop_column("ruta_archivo")

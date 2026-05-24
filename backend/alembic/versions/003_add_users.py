"""Agregar tabla users y columna user_id a transacciones y batches

Revision ID: 003
Revises: 002
Create Date: 2025-01-01 00:02:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tabla de usuarios
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("es_admin", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ultimo_login", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # Agregar user_id a upload_batches
    op.add_column("upload_batches", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_index("ix_upload_batches_user_id", "upload_batches", ["user_id"])
    op.create_foreign_key("fk_batches_user", "upload_batches", "users", ["user_id"], ["id"])

    # Agregar user_id a transactions
    op.add_column("transactions", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"])
    op.create_foreign_key("fk_transactions_user", "transactions", "users", ["user_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_transactions_user", "transactions", type_="foreignkey")
    op.drop_index("ix_transactions_user_id", "transactions")
    op.drop_column("transactions", "user_id")

    op.drop_constraint("fk_batches_user", "upload_batches", type_="foreignkey")
    op.drop_index("ix_upload_batches_user_id", "upload_batches")
    op.drop_column("upload_batches", "user_id")

    op.drop_table("users")

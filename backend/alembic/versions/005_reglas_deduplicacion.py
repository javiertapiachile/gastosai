"""Tabla de reglas de clasificación y hash de deduplicación en batches

Revision ID: 005
Revises: 004
Create Date: 2025-01-01 00:04:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tabla de reglas de clasificación manual
    op.create_table(
        "clasificacion_reglas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patron", sa.String(200), nullable=False),
        sa.Column("tipo_match", sa.String(20), nullable=False, server_default="contiene"),
        sa.Column("categoria_id", sa.Integer(), nullable=False),
        sa.Column("descripcion_regla", sa.String(200), nullable=True),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("prioridad", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["categoria_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("ix_clasificacion_reglas_id", "clasificacion_reglas", ["id"])
    op.create_index("ix_clasificacion_reglas_user_id", "clasificacion_reglas", ["user_id"])

    # Hash de contenido para deduplicación de archivos
    op.add_column(
        "upload_batches",
        sa.Column("hash_contenido", sa.String(64), nullable=True)
    )
    op.create_index("ix_upload_batches_hash", "upload_batches", ["hash_contenido"])


def downgrade() -> None:
    op.drop_index("ix_upload_batches_hash", "upload_batches")
    op.drop_column("upload_batches", "hash_contenido")
    op.drop_index("ix_clasificacion_reglas_user_id", "clasificacion_reglas")
    op.drop_index("ix_clasificacion_reglas_id", "clasificacion_reglas")
    op.drop_table("clasificacion_reglas")

"""Tabla classification_cache para caché de clasificaciones LLM

Revision ID: 002
Revises: 001
Create Date: 2025-01-01 00:01:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "classification_cache",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hash_descripcion", sa.String(64), nullable=False),
        sa.Column("descripcion_normalizada", sa.String(200), nullable=False),
        sa.Column("categoria", sa.String(100), nullable=False),
        sa.Column("comercio_limpio", sa.String(200), nullable=False),
        sa.Column("confianza", sa.Float(), nullable=False, server_default="0.8"),
        sa.Column("proveedor_llm", sa.String(100), nullable=False),
        sa.Column("usos", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_classification_cache_id", "classification_cache", ["id"])
    op.create_index(
        "ix_classification_cache_hash",
        "classification_cache",
        ["hash_descripcion"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("classification_cache")

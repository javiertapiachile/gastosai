"""Esquema inicial: categorías, transacciones, upload_batches

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tabla de categorías
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("color", sa.String(7), nullable=False, server_default="#888780"),
        sa.Column("icono", sa.String(50), nullable=False, server_default="ti-tag"),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("es_sistema", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_categories_id", "categories", ["id"])
    op.create_index("ix_categories_nombre", "categories", ["nombre"], unique=True)

    # Tabla de lotes de carga
    op.create_table(
        "upload_batches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre_archivo", sa.String(255), nullable=False),
        sa.Column("tipo_archivo", sa.String(10), nullable=False),
        sa.Column(
            "estado",
            sa.Enum("pendiente", "procesando", "clasificando", "completado", "error", name="batchstatus"),
            nullable=False,
            server_default="pendiente",
        ),
        sa.Column("total_transacciones", sa.Integer(), server_default="0"),
        sa.Column("transacciones_procesadas", sa.Integer(), server_default="0"),
        sa.Column("progreso", sa.Float(), server_default="0.0"),
        sa.Column("mensaje_error", sa.String(500), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completado_en", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_upload_batches_id", "upload_batches", ["id"])

    # Tabla de transacciones
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("descripcion_original", sa.String(500), nullable=False),
        sa.Column("monto", sa.Float(), nullable=False),
        sa.Column("es_cargo", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("rut_comercio", sa.String(20), nullable=True),
        sa.Column("comercio_limpio", sa.String(200), nullable=True),
        sa.Column("descripcion_limpia", sa.String(200), nullable=True),
        sa.Column("categoria_id", sa.Integer(), nullable=True),
        sa.Column("confianza_clasificacion", sa.Float(), nullable=True),
        sa.Column("clasificado_por_cache", sa.Boolean(), server_default="0"),
        sa.Column("revisado_por_usuario", sa.Boolean(), server_default="0"),
        sa.Column("batch_id", sa.Integer(), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["categoria_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["batch_id"], ["upload_batches.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_transactions_id", "transactions", ["id"])
    op.create_index("ix_transactions_fecha", "transactions", ["fecha"])
    op.create_index("ix_transactions_categoria_id", "transactions", ["categoria_id"])
    op.create_index("ix_transactions_batch_id", "transactions", ["batch_id"])

    # Insertar categorías base del sistema (no se pueden borrar)
    categorias_base = [
        ("Alimentación",    "#1D9E75", "ti-shopping-cart",    True),
        ("Transporte",      "#378ADD", "ti-car",              True),
        ("Compras",         "#EF9F27", "ti-package",          True),
        ("Entretenimiento", "#7F77DD", "ti-device-tv",        True),
        ("Salud",           "#D85A30", "ti-heart",            True),
        ("Servicios",       "#5DCAA5", "ti-bolt",             True),
        ("Educación",       "#185FA5", "ti-book",             True),
        ("Viajes",          "#E85D24", "ti-plane",            True),
        ("Hogar",           "#639922", "ti-home",             True),
        ("Sin categoría",   "#888780", "ti-question-mark",    True),
    ]

    op.bulk_insert(
        sa.table(
            "categories",
            sa.column("nombre", sa.String),
            sa.column("color", sa.String),
            sa.column("icono", sa.String),
            sa.column("es_sistema", sa.Boolean),
        ),
        [
            {"nombre": n, "color": c, "icono": i, "es_sistema": s}
            for n, c, i, s in categorias_base
        ],
    )


def downgrade() -> None:
    op.drop_table("transactions")
    op.drop_table("upload_batches")
    op.drop_table("categories")

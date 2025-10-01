"""Initial schema with proyectos, etapas, and pedidos

Revision ID: e33c335d25f7
Revises:
Create Date: 2025-10-01 00:53:11.922015

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e33c335d25f7'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - create proyectos, etapas, and pedidos tables."""

    # Create ENUM types using raw SQL to avoid conflicts
    # These will be created before the tables
    op.execute("CREATE TYPE estadoproyecto AS ENUM ('borrador', 'en_planificacion', 'buscando_financiamiento', 'en_ejecucion', 'completo')")
    op.execute("CREATE TYPE tipopedido AS ENUM ('economico', 'materiales', 'mano_obra')")

    # Create proyectos table
    op.create_table(
        'proyectos',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('titulo', sa.String(length=255), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=False),
        sa.Column('tipo', sa.String(length=100), nullable=False),
        sa.Column('pais', sa.String(length=100), nullable=False),
        sa.Column('provincia', sa.String(length=100), nullable=False),
        sa.Column('ciudad', sa.String(length=100), nullable=False),
        sa.Column('barrio', sa.String(length=100), nullable=True),
        sa.Column('bonita_case_id', sa.String(length=255), nullable=True),
        sa.Column('bonita_process_instance_id', sa.Integer(), nullable=True),
        sa.Column('estado', postgresql.ENUM('borrador', 'en_planificacion', 'buscando_financiamiento', 'en_ejecucion', 'completo', name='estadoproyecto', create_type=False), nullable=False),
        sa.Column('fecha_creacion', sa.DateTime(), nullable=False),
        sa.Column('fecha_actualizacion', sa.DateTime(), nullable=False),
    )

    # Create etapas table
    op.create_table(
        'etapas',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('nombre', sa.String(length=255), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=False),
        sa.Column('fecha_inicio', sa.Date(), nullable=False),
        sa.Column('fecha_fin', sa.Date(), nullable=False),
        sa.Column('proyecto_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['proyecto_id'], ['proyectos.id'], ondelete='CASCADE'),
    )

    # Create pedidos table
    op.create_table(
        'pedidos',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tipo', postgresql.ENUM('economico', 'materiales', 'mano_obra', name='tipopedido', create_type=False), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=False),
        sa.Column('monto', sa.Float(), nullable=True),
        sa.Column('moneda', sa.String(length=10), nullable=True),
        sa.Column('cantidad', sa.Integer(), nullable=True),
        sa.Column('unidad', sa.String(length=50), nullable=True),
        sa.Column('etapa_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['etapa_id'], ['etapas.id'], ondelete='CASCADE'),
    )


def downgrade() -> None:
    """Downgrade schema - drop all tables and enums."""
    op.drop_table('pedidos')
    op.drop_table('etapas')
    op.drop_table('proyectos')

    # Drop ENUM types
    op.execute('DROP TYPE IF EXISTS tipopedido')
    op.execute('DROP TYPE IF EXISTS estadoproyecto')

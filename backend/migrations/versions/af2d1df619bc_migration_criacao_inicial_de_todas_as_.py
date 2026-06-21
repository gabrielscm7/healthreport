"""migration: criacao inicial de todas as tabelas

Revision ID: af2d1df619bc
Revises: 0002_exam_comparisons
Create Date: 2026-06-21 01:38:52.081949
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'af2d1df619bc'
down_revision: Union[str, None] = '0002_exam_comparisons'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
   
    # Criação da tabela de Usuários
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),  # Ajustado para string base do enum
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('crm', sa.String(length=20), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('two_fa_enabled', sa.Boolean(), default=False),
        sa.Column('two_fa_secret', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_crm', 'users', ['crm'])

    # Criação da tabela de Pacientes
    op.create_table(
        'patients',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('cpf_hash', sa.String(length=255), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('contact_phone', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cpf_hash'),
        sa.CheckConstraint("full_name != ''", name="no_plain_text")
    )
    op.create_index('idx_patients_cpf_hash', 'patients', ['cpf_hash'])


def downgrade() -> None:
    pass

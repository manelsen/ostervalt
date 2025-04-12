"""Estrutura inicial do banco de dados

Revision ID: d1495bdc3dce
Revises: 
Create Date: 2025-04-12 12:55:39.469075

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1495bdc3dce'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('itens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(), nullable=False),
    sa.Column('raridade', sa.String(), nullable=False),
    sa.Column('valor', sa.Integer(), nullable=False),
    sa.Column('descricao', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_itens_id'), 'itens', ['id'], unique=False)
    op.create_table('personagens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(), nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('servidor_id', sa.Integer(), nullable=False),
    sa.Column('marcos', sa.Integer(), nullable=True),
    sa.Column('dinheiro', sa.Integer(), nullable=True),
    sa.Column('nivel', sa.Integer(), nullable=True),
    sa.Column('ultimo_trabalho', sa.DateTime(), nullable=True),
    sa.Column('ultimo_crime', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_personagens_id'), 'personagens', ['id'], unique=False)
    op.create_table('itens_inventario',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('personagem_id', sa.Integer(), nullable=True),
    sa.Column('item_id', sa.Integer(), nullable=True),
    sa.Column('quantidade', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['item_id'], ['itens.id'], ),
    sa.ForeignKeyConstraint(['personagem_id'], ['personagens.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_itens_inventario_id'), 'itens_inventario', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_itens_inventario_id'), table_name='itens_inventario')
    op.drop_table('itens_inventario')
    op.drop_index(op.f('ix_personagens_id'), table_name='personagens')
    op.drop_table('personagens')
    op.drop_index(op.f('ix_itens_id'), table_name='itens')
    op.drop_table('itens')
    # ### end Alembic commands ###

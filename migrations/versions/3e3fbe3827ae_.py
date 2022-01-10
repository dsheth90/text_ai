"""empty message

Revision ID: 3e3fbe3827ae
Revises: 5c1eae6fa7fa
Create Date: 2021-12-26 15:53:18.002254

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3e3fbe3827ae'
down_revision = '5c1eae6fa7fa'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('task', sa.Column('model_id_fk', sa.String(length=80), nullable=True))
    op.add_column('task', sa.Column('user_id_fk', sa.String(length=80), nullable=True))
    op.drop_constraint(None, 'task', type_='foreignkey')
    op.create_foreign_key(None, 'task', 'models', ['model_id_fk'], ['model_id'])
    op.create_foreign_key(None, 'task', 'users', ['user_id_fk'], ['id'])
    op.drop_column('task', 'model_name_fk')
    op.drop_column('task', 'model_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('task', sa.Column('model_id', sa.VARCHAR(), nullable=True))
    op.add_column('task', sa.Column('model_name_fk', sa.VARCHAR(length=80), nullable=True))
    op.drop_constraint(None, 'task', type_='foreignkey')
    op.drop_constraint(None, 'task', type_='foreignkey')
    op.create_foreign_key(None, 'task', 'models', ['model_name_fk'], ['model_name'])
    op.drop_column('task', 'user_id_fk')
    op.drop_column('task', 'model_id_fk')
    # ### end Alembic commands ###

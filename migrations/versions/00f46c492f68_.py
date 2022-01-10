"""empty message

Revision ID: 00f46c492f68
Revises: 884790144d85
Create Date: 2021-12-29 16:33:35.554461

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '00f46c492f68'
down_revision = '884790144d85'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('task_result',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('job_id_fk', sa.String(length=80), nullable=True),
    sa.Column('text_id', sa.Integer(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('emotion', sa.String(length=80), nullable=True),
    sa.Column('created_on', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['job_id_fk'], ['task.job_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('models', schema=None) as batch_op:
        batch_op.add_column(sa.Column('error_message', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('is_error', sa.Integer(), nullable=False))

    with op.batch_alter_table('task', schema=None) as batch_op:
        batch_op.add_column(sa.Column('error_message', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('is_error', sa.Integer(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('task', schema=None) as batch_op:
        batch_op.drop_column('is_error')
        batch_op.drop_column('error_message')

    with op.batch_alter_table('models', schema=None) as batch_op:
        batch_op.drop_column('is_error')
        batch_op.drop_column('error_message')

    op.drop_table('task_result')
    # ### end Alembic commands ###

"""Add AI generation fields to itinerary and new columns

Revision ID: 002_ai_itinerary_fields
Revises: 001_initial_schema
Create Date: 2026-09-06

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_ai_itinerary_fields'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make itinerary.user_id nullable
    op.alter_column('itineraries', 'user_id', nullable=True)
    op.alter_column('itineraries', 'start_date', nullable=True)
    op.alter_column('itineraries', 'end_date', nullable=True)

    # Add AI generation fields
    op.add_column('itineraries', sa.Column('summary', sa.Text(), nullable=True))
    op.add_column('itineraries', sa.Column('duration_days', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('itineraries', sa.Column('travel_style', sa.String(50), nullable=True))
    op.add_column('itineraries', sa.Column('budget_level', sa.String(50), nullable=True))
    op.add_column('itineraries', sa.Column('day_plans', sa.JSON(), nullable=True))
    op.add_column('itineraries', sa.Column('total_estimated_cost_usd', sa.Numeric(12, 2), nullable=True))

    # Drop the date check constraint if it exists (it may not since it was never applied)
    try:
        op.drop_constraint('ck_itineraries_dates', 'itineraries', type_='check')
    except Exception:
        pass


def downgrade() -> None:
    op.drop_column('itineraries', 'total_estimated_cost_usd')
    op.drop_column('itineraries', 'day_plans')
    op.drop_column('itineraries', 'budget_level')
    op.drop_column('itineraries', 'travel_style')
    op.drop_column('itineraries', 'duration_days')
    op.drop_column('itineraries', 'summary')

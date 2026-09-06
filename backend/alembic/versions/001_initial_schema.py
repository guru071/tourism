"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-06 18:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('role', sa.String(50), nullable=False, server_default='tourist'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('phone_number', sa.String(50), nullable=True),
        sa.Column('preferred_language', sa.String(10), nullable=False, server_default='en'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('uq_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_role', 'users', ['role'])
    op.create_index('ix_users_is_active', 'users', ['is_active'])

    # 2. destinations
    op.create_table(
        'destinations',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('country', sa.String(100), nullable=False),
        sa.Column('region', sa.String(100), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('latitude', sa.Numeric(10, 7), nullable=True),
        sa.Column('longitude', sa.Numeric(10, 7), nullable=True),
        sa.Column('timezone', sa.String(50), nullable=False, server_default='UTC'),
        sa.Column('image_urls', sa.JSON(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('tags', sa.JSON(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('uq_destinations_slug', 'destinations', ['slug'], unique=True)
    op.create_index('ix_destinations_country', 'destinations', ['country'])
    op.create_index('ix_destinations_region', 'destinations', ['region'])
    op.create_index('ix_destinations_is_active', 'destinations', ['is_active'])

    # 3. operators
    op.create_table(
        'operators',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', sa.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('business_name', sa.String(255), nullable=False),
        sa.Column('business_type', sa.String(50), nullable=False, server_default='agency'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('registration_number', sa.String(100), nullable=True),
        sa.Column('contact_email', sa.String(255), nullable=False),
        sa.Column('contact_phone', sa.String(50), nullable=True),
        sa.Column('website_url', sa.String(255), nullable=True),
        sa.Column('verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('verification_status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('uq_operators_user_id', 'operators', ['user_id'], unique=True)
    op.create_index('ix_operators_business_type', 'operators', ['business_type'])
    op.create_index('ix_operators_verification_status', 'operators', ['verification_status'])

    # 4. listings
    op.create_table(
        'listings',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('operator_id', sa.UUID(as_uuid=True), sa.ForeignKey('operators.id', ondelete='CASCADE'), nullable=False),
        sa.Column('destination_id', sa.UUID(as_uuid=True), sa.ForeignKey('destinations.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('base_price', sa.Numeric(12, 2), nullable=False, server_default='0.00'),
        sa.Column('price', sa.Numeric(12, 2), nullable=True),
        sa.Column('currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('availability', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('duration_hours', sa.Numeric(5, 2), nullable=True),
        sa.Column('latitude', sa.Numeric(10, 7), nullable=True),
        sa.Column('longitude', sa.Numeric(10, 7), nullable=True),
        sa.Column('amenities', sa.JSON(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('images', sa.JSON(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('rating_average', sa.Numeric(3, 2), nullable=False, server_default='0.00'),
        sa.Column('review_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('base_price >= 0', name='ck_listings_base_price'),
        sa.CheckConstraint('rating_average >= 0 AND rating_average <= 5', name='ck_listings_rating_average'),
    )
    op.create_index('uq_listings_slug', 'listings', ['slug'], unique=True)
    op.create_index('ix_listings_operator_id', 'listings', ['operator_id'])
    op.create_index('ix_listings_destination_id', 'listings', ['destination_id'])
    op.create_index('ix_listings_category', 'listings', ['category'])
    op.create_index('ix_listings_is_active', 'listings', ['is_active'])

    # 5. itineraries
    op.create_table(
        'itineraries',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', sa.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('destination_id', sa.UUID(as_uuid=True), sa.ForeignKey('destinations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('budget_limit', sa.Numeric(12, 2), nullable=True),
        sa.Column('currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('is_ai_generated', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('ai_prompt_context', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='draft'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('start_date <= end_date', name='ck_itineraries_dates'),
    )
    op.create_index('ix_itineraries_user_id', 'itineraries', ['user_id'])
    op.create_index('ix_itineraries_destination_id', 'itineraries', ['destination_id'])
    op.create_index('ix_itineraries_status', 'itineraries', ['status'])

    # 6. itinerary_items
    op.create_table(
        'itinerary_items',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('itinerary_id', sa.UUID(as_uuid=True), sa.ForeignKey('itineraries.id', ondelete='CASCADE'), nullable=False),
        sa.Column('listing_id', sa.UUID(as_uuid=True), sa.ForeignKey('listings.id', ondelete='SET NULL'), nullable=True),
        sa.Column('day_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=True),
        sa.Column('end_time', sa.Time(), nullable=True),
        sa.Column('estimated_cost', sa.Numeric(12, 2), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('day_number >= 1', name='ck_itinerary_items_day_number'),
        sa.CheckConstraint('order_index >= 0', name='ck_itinerary_items_order_index'),
    )
    op.create_index('ix_itinerary_items_itinerary_id', 'itinerary_items', ['itinerary_id'])
    op.create_index('ix_itinerary_items_listing_id', 'itinerary_items', ['listing_id'])

    # 7. bookings
    op.create_table(
        'bookings',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', sa.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('listing_id', sa.UUID(as_uuid=True), sa.ForeignKey('listings.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('itinerary_id', sa.UUID(as_uuid=True), sa.ForeignKey('itineraries.id', ondelete='SET NULL'), nullable=True),
        sa.Column('booking_reference', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('guests_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('total_price', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('payment_status', sa.String(50), nullable=False, server_default='unpaid'),
        sa.Column('payment_transaction_id', sa.String(100), nullable=True),
        sa.Column('special_requests', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('start_date <= end_date', name='ck_bookings_dates'),
        sa.CheckConstraint('guests_count >= 1', name='ck_bookings_guests'),
        sa.CheckConstraint('total_price >= 0', name='ck_bookings_price'),
    )
    op.create_index('uq_bookings_reference', 'bookings', ['booking_reference'], unique=True)
    op.create_index('ix_bookings_user_id', 'bookings', ['user_id'])
    op.create_index('ix_bookings_listing_id', 'bookings', ['listing_id'])
    op.create_index('ix_bookings_status', 'bookings', ['status'])

    # 8. reviews
    op.create_table(
        'reviews',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', sa.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('listing_id', sa.UUID(as_uuid=True), sa.ForeignKey('listings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('booking_id', sa.UUID(as_uuid=True), sa.ForeignKey('bookings.id', ondelete='SET NULL'), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='ck_reviews_rating'),
    )
    op.create_index('uq_reviews_booking_id', 'reviews', ['booking_id'], unique=True)
    op.create_index('ix_reviews_listing_id', 'reviews', ['listing_id'])
    op.create_index('ix_reviews_user_id', 'reviews', ['user_id'])


def downgrade() -> None:
    # Drop tables in reverse dependency order
    op.drop_table('reviews')
    op.drop_table('bookings')
    op.drop_table('itinerary_items')
    op.drop_table('itineraries')
    op.drop_table('listings')
    op.drop_table('operators')
    op.drop_table('destinations')
    op.drop_table('users')

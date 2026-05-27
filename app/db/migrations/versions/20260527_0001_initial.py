"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-27
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("discord_id", sa.BigInteger(), nullable=False),
        sa.Column("discord_username", sa.Text()),
        sa.Column("discord_avatar", sa.Text()),
        sa.Column("email", sa.Text()),
        sa.Column("oauth_access_token_enc", sa.LargeBinary()),
        sa.Column("oauth_refresh_token_enc", sa.LargeBinary()),
        sa.Column("oauth_expires_at", postgresql.TIMESTAMP(timezone=True)),
        sa.Column(
            "preferences",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("plan", sa.String(16), nullable=False, server_default="free"),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("deleted_at", postgresql.TIMESTAMP(timezone=True)),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("discord_id", name="uq_users_discord_id"),
    )

    op.create_table(
        "servers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.Text()),
        sa.Column("icon_hash", sa.Text()),
        sa.Column("tracker_role_id", sa.BigInteger()),
        sa.Column("default_alert_channel_id", sa.BigInteger()),
        sa.Column("default_alert_role_id", sa.BigInteger()),
        sa.Column("region_default", sa.CHAR(2)),
        sa.Column("plan", sa.String(16), nullable=False, server_default="free"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "joined_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("removed_at", postgresql.TIMESTAMP(timezone=True)),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_servers"),
        sa.UniqueConstraint("guild_id", name="uq_servers_guild_id"),
    )

    op.create_table(
        "server_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("server_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "has_tracker_role", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("last_seen_at", postgresql.TIMESTAMP(timezone=True)),
        sa.PrimaryKeyConstraint("id", name="pk_server_memberships"),
        sa.ForeignKeyConstraint(
            ["server_id"], ["servers.id"], name="fk_server_memberships_server_id_servers"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_server_memberships_user_id_users"
        ),
        sa.UniqueConstraint(
            "server_id", "user_id", name="uq_server_memberships_server_id_user_id"
        ),
    )
    op.create_index(
        "ix_server_memberships_server_id", "server_memberships", ["server_id"]
    )
    op.create_index("ix_server_memberships_user_id", "server_memberships", ["user_id"])

    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("domain", sa.Text(), nullable=False),
        sa.Column("region", sa.CHAR(2)),
        sa.Column("title", sa.Text()),
        sa.Column("image_url", sa.Text()),
        sa.Column("brand", sa.Text()),
        sa.Column("gtin", sa.Text()),
        sa.Column("mpn", sa.Text()),
        sa.Column("asin", sa.Text()),
        sa.Column("currency", sa.CHAR(3)),
        sa.Column("last_known_price", sa.Numeric(12, 2)),
        sa.Column("last_known_in_stock", sa.Boolean()),
        sa.Column("last_scraped_at", postgresql.TIMESTAMP(timezone=True)),
        sa.Column("last_scrape_status", sa.String(16)),
        sa.Column("scrape_tier", sa.SmallInteger()),
        sa.Column(
            "circuit_state", sa.String(16), nullable=False, server_default="closed"
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_products"),
        sa.UniqueConstraint("source_url", name="uq_products_source_url"),
    )
    op.create_index("ix_products_domain", "products", ["domain"])
    op.create_index("ix_products_last_scraped_at", "products", ["last_scraped_at"])
    op.create_index(
        "ix_products_gtin", "products", ["gtin"], postgresql_where=sa.text("gtin IS NOT NULL")
    )
    op.create_index(
        "ix_products_mpn", "products", ["mpn"], postgresql_where=sa.text("mpn IS NOT NULL")
    )
    op.create_index(
        "ix_products_asin", "products", ["asin"], postgresql_where=sa.text("asin IS NOT NULL")
    )

    op.create_table(
        "watches",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("short_id", sa.String(8), nullable=False),
        sa.Column("server_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("added_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "alert_rules", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("alert_channel_id", sa.BigInteger()),
        sa.Column("alert_role_id", sa.BigInteger()),
        sa.Column("region_override", sa.CHAR(2)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("paused_at", postgresql.TIMESTAMP(timezone=True)),
        sa.Column("last_alert_at", postgresql.TIMESTAMP(timezone=True)),
        sa.Column("removed_at", postgresql.TIMESTAMP(timezone=True)),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_watches"),
        sa.UniqueConstraint("short_id", name="uq_watches_short_id"),
        sa.UniqueConstraint(
            "server_id", "product_id", name="uq_watches_server_id_product_id"
        ),
        sa.ForeignKeyConstraint(
            ["server_id"], ["servers.id"], name="fk_watches_server_id_servers"
        ),
        sa.ForeignKeyConstraint(
            ["added_by_user_id"], ["users.id"], name="fk_watches_added_by_user_id_users"
        ),
        sa.ForeignKeyConstraint(
            ["product_id"], ["products.id"], name="fk_watches_product_id_products"
        ),
    )
    op.create_index("ix_watches_short_id", "watches", ["short_id"])
    op.create_index("ix_watches_server_id", "watches", ["server_id"])
    op.create_index("ix_watches_added_by_user_id", "watches", ["added_by_user_id"])
    op.create_index("ix_watches_product_id", "watches", ["product_id"])
    op.create_index(
        "ix_watches_is_active",
        "watches",
        ["is_active"],
        postgresql_where=sa.text("is_active = true"),
    )

    op.create_table(
        "price_snapshots",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "observed_at", postgresql.TIMESTAMP(timezone=True), nullable=False
        ),
        sa.Column("price", sa.Numeric(12, 2)),
        sa.Column("currency", sa.CHAR(3)),
        sa.Column("in_stock", sa.Boolean()),
        sa.Column("source_tier", sa.SmallInteger()),
        sa.Column("scrape_status", sa.String(16)),
        sa.PrimaryKeyConstraint("id", name="pk_price_snapshots"),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name="fk_price_snapshots_product_id_products",
        ),
    )
    op.create_index(
        "ix_price_snapshots_observed_at", "price_snapshots", ["observed_at"]
    )
    op.create_index(
        "ix_price_snapshots_product_time",
        "price_snapshots",
        ["product_id", sa.text("observed_at DESC")],
    )

    op.create_table(
        "alert_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("watch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rule_type", sa.String(16), nullable=False),
        sa.Column(
            "triggered_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("previous_price", sa.Numeric(12, 2)),
        sa.Column("new_price", sa.Numeric(12, 2)),
        sa.Column("previous_in_stock", sa.Boolean()),
        sa.Column("new_in_stock", sa.Boolean()),
        sa.Column(
            "payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column(
            "delivery_status",
            sa.String(32),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("delivery_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("delivered_at", postgresql.TIMESTAMP(timezone=True)),
        sa.Column("last_error", sa.Text()),
        sa.PrimaryKeyConstraint("id", name="pk_alert_events"),
        sa.ForeignKeyConstraint(
            ["watch_id"], ["watches.id"], name="fk_alert_events_watch_id_watches"
        ),
    )
    op.create_index(
        "ix_alert_events_watch_time",
        "alert_events",
        ["watch_id", sa.text("triggered_at DESC")],
    )
    op.create_index(
        "ix_alert_events_pending",
        "alert_events",
        ["id"],
        postgresql_where=sa.text("delivery_status = 'pending'"),
    )

    op.create_table(
        "fx_rates",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("base", sa.CHAR(3), nullable=False, server_default="USD"),
        sa.Column(
            "rates", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column(
            "fetched_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_fx_rates"),
        sa.UniqueConstraint("date", name="uq_fx_rates_date"),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("actor_type", sa.String(16), nullable=False),
        sa.Column("actor_id", sa.Text()),
        sa.Column("server_id", postgresql.UUID(as_uuid=True)),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("target_type", sa.Text()),
        sa.Column("target_id", sa.Text()),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_audit_log"),
        sa.ForeignKeyConstraint(
            ["server_id"], ["servers.id"], name="fk_audit_log_server_id_servers"
        ),
    )
    op.create_index("ix_audit_log_server_id", "audit_log", ["server_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_log_server_id", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_table("fx_rates")

    op.drop_index("ix_alert_events_pending", table_name="alert_events")
    op.drop_index("ix_alert_events_watch_time", table_name="alert_events")
    op.drop_table("alert_events")

    op.drop_index("ix_price_snapshots_product_time", table_name="price_snapshots")
    op.drop_index("ix_price_snapshots_observed_at", table_name="price_snapshots")
    op.drop_table("price_snapshots")

    op.drop_index("ix_watches_is_active", table_name="watches")
    op.drop_index("ix_watches_product_id", table_name="watches")
    op.drop_index("ix_watches_added_by_user_id", table_name="watches")
    op.drop_index("ix_watches_server_id", table_name="watches")
    op.drop_index("ix_watches_short_id", table_name="watches")
    op.drop_table("watches")

    op.drop_index("ix_products_asin", table_name="products")
    op.drop_index("ix_products_mpn", table_name="products")
    op.drop_index("ix_products_gtin", table_name="products")
    op.drop_index("ix_products_last_scraped_at", table_name="products")
    op.drop_index("ix_products_domain", table_name="products")
    op.drop_table("products")

    op.drop_index("ix_server_memberships_user_id", table_name="server_memberships")
    op.drop_index("ix_server_memberships_server_id", table_name="server_memberships")
    op.drop_table("server_memberships")

    op.drop_table("servers")
    op.drop_table("users")

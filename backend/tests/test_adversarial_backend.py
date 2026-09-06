"""
Adversarial Verification Suite for AI Tourism Ecosystem Backend & Data Models.

This suite stress-tests:
1. FastAPI /health and /api/v1 response structures, headers, and status codes.
2. Route negatives (404 on invalid paths, 405 on disallowed HTTP methods: POST/PUT/DELETE/PATCH).
3. CORS headers, preflight handling, and security behavior under wildcard credentials.
4. SQLAlchemy 2.0 domain model integrity:
   - configure_mappers() compilation
   - Table naming and Base.metadata binding
   - UUID primary keys and foreign keys
   - Foreign key constraint definitions and ondelete cascade actions
   - CheckConstraint definitions and database-level enforcement
   - In-memory relationship graph traversal
   - Session persistence and Core default value generation
   - UniqueConstraint database-level enforcement
   - In-memory SQLite DDL compilation (create_all / drop_all)
5. Alembic migration script integrity:
   - 001_initial_schema.py structure, callable upgrade/downgrade
   - Table and column parity between models and migration
   - Downgrade drop order topological sort
   - Offline SQL generation for both upgrade and downgrade
"""

import ast
import importlib.util
import os
import subprocess
import sys
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Dict, List, Set

import pytest
from sqlalchemy import Uuid, create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, configure_mappers

from app.core.config import settings
from app.core.database import Base
from app.main import app
from app.models import (
    Booking,
    Destination,
    Itinerary,
    ItineraryItem,
    Listing,
    Operator,
    Review,
    User,
)


# ============================================================================
# TIER A: FASTAPI ROUTING, HEADERS, 404, 405, AND RESILIENCE
# ============================================================================
class TestFastAPIEndpointsAndErrors:
    """Stress-test endpoint status codes, headers, and method restrictions."""

    def test_health_response_structure_and_types(self, client):
        """GET /health must return 200 OK with strict JSON schema."""
        resp = client.get("/health")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assert "application/json" in resp.headers.get("content-type", "").lower()

        data = resp.json()
        assert isinstance(data, dict), "Response payload must be a JSON object"
        assert data.get("status") == "ok", f"Expected status 'ok', got {data.get('status')}"
        assert isinstance(data.get("version"), str) and len(data["version"]) > 0
        assert "services" in data, "services mapping must be present"
        assert isinstance(data["services"], dict)
        assert "database" in data["services"]
        assert "redis" in data["services"]
        assert data["services"]["database"] in ("healthy", "unreachable")
        assert data["services"]["redis"] in ("healthy", "unreachable")

    def test_health_query_param_resilience(self, client):
        """Unexpected query parameters and SQL injection attempts must not fail /health."""
        malicious_queries = [
            "?test=1",
            "?foo=bar&baz=qux",
            "?id=' OR '1'='1",
            "?drop=table%20users;--",
            "?limit=9999999999999999999999",
            "?search=<script>alert(1)</script>",
        ]
        for query in malicious_queries:
            resp = client.get(f"/health{query}")
            assert resp.status_code == 200, f"Failed on query: {query} with code {resp.status_code}"
            data = resp.json()
            assert data.get("status") == "ok"

    def test_api_v1_root_response(self, client):
        """GET /api/v1 and /api/v1/ must both return 200 OK with welcome message."""
        for path in ("/api/v1", "/api/v1/"):
            resp = client.get(path)
            assert resp.status_code == 200, f"Path {path} returned {resp.status_code}"
            assert "application/json" in resp.headers.get("content-type", "").lower()
            data = resp.json()
            assert data.get("message") == "Welcome to the AI Tourism API v1"
            assert data.get("status") == "active"

    def test_api_v1_health_subrouter_parity(self, client):
        """GET /api/v1/health mounted subrouter must match /health structure."""
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "ok"
        assert "services" in data
        assert "database" in data["services"]
        assert "redis" in data["services"]

    @pytest.mark.parametrize(
        "invalid_path",
        [
            "/nonexistent",
            "/api/v1/nonexistent",
            "/api/v2",
            "/admin/debug",
            "/api/v1/admin/supersecret",
            "/health/deeply/nested/child",
            "/static/main.css",
            "/favicon.ico",
        ],
    )
    def test_non_existent_routes_return_404(self, client, invalid_path: str):
        """Unregistered paths must strictly return 404 Not Found."""
        resp = client.get(invalid_path)
        assert resp.status_code == 404, f"Expected 404 for '{invalid_path}', got {resp.status_code}"
        assert "application/json" in resp.headers.get("content-type", "").lower()

    @pytest.mark.parametrize(
        "endpoint,method",
        [
            ("/health", "post"),
            ("/health", "put"),
            ("/health", "delete"),
            ("/health", "patch"),
            ("/api/v1", "post"),
            ("/api/v1", "put"),
            ("/api/v1", "delete"),
            ("/api/v1", "patch"),
            ("/api/v1/health", "post"),
            ("/api/v1/health", "put"),
            ("/api/v1/health", "delete"),
            ("/api/v1/health", "patch"),
        ],
    )
    def test_invalid_http_methods_return_405(self, client, endpoint: str, method: str):
        """State-mutating HTTP verbs on read-only endpoints must return 405 Method Not Allowed."""
        caller = getattr(client, method)
        if method in ("post", "put", "patch"):
            resp = caller(endpoint, json={"foo": "bar"})
        else:
            resp = caller(endpoint)
        assert resp.status_code == 405, (
            f"Expected 405 for {method.upper()} {endpoint}, got {resp.status_code}: {resp.text}"
        )


# ============================================================================
# TIER B: CORS HEADERS & PREFLIGHT HANDLING
# ============================================================================
class TestCORSAndPreflightHandling:
    """Stress-test CORS preflight and actual origin handling."""

    def test_cors_preflight_standard_frontend_origin(self, client):
        """OPTIONS preflight from standard Next.js frontend port 3000."""
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization, Content-Type",
        }
        resp = client.options("/health", headers=headers)
        assert resp.status_code == 200, f"Expected 200 on OPTIONS, got {resp.status_code}"
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"
        assert resp.headers.get("access-control-allow-credentials") == "true"
        allow_methods = resp.headers.get("access-control-allow-methods", "")
        assert "GET" in allow_methods or "*" in allow_methods

    def test_cors_preflight_on_api_v1(self, client):
        """OPTIONS preflight on /api/v1 root route."""
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        }
        resp = client.options("/api/v1", headers=headers)
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"

    def test_cors_get_request_includes_allow_origin_header(self, client):
        """Direct GET request with Origin header receives Access-Control-Allow-Origin."""
        resp = client.get("/health", headers={"Origin": "http://localhost:3000"})
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"

    def test_cors_wildcard_credential_behavior_audit(self, client):
        """
        Adversarial Security Probe:
        When settings.CORS_ORIGINS=['*'] and allow_credentials=True, Starlette CORSMiddleware
        reflects the untrusted Origin in Access-Control-Allow-Origin rather than rejecting it.
        This test asserts the empirical behavior for documentation in the audit report.
        """
        untrusted_origin = "https://evil-hacker.com"
        resp = client.options(
            "/health",
            headers={
                "Origin": untrusted_origin,
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.status_code == 200
        reflected_origin = resp.headers.get("access-control-allow-origin")
        assert reflected_origin == untrusted_origin, (
            f"Expected reflected origin '{untrusted_origin}', got '{reflected_origin}'"
        )
        assert resp.headers.get("access-control-allow-credentials") == "true"


# ============================================================================
# TIER C: SQLALCHEMY 2.0 DOMAIN MODEL INTEGRITY
# ============================================================================
class TestSQLAlchemyModelIntegrity:
    """Verify DeclarativeBase, metadata binding, table names, UUID columns, and FKs."""

    EXPECTED_TABLES = {
        "users",
        "destinations",
        "operators",
        "listings",
        "itineraries",
        "itinerary_items",
        "bookings",
        "reviews",
    }

    def test_configure_mappers_compiles_cleanly(self):
        """
        SQLAlchemy configure_mappers() compiles all model relationships, back_populates,
        and foreign key targets. If any typo or circular invalid mapping exists, this throws.
        """
        try:
            configure_mappers()
        except Exception as e:
            pytest.fail(f"configure_mappers() failed: {e}")

    def test_metadata_tables_and_naming(self):
        """All 8 expected domain tables must be registered in Base.metadata."""
        registered_tables = set(Base.metadata.tables.keys())
        missing = self.EXPECTED_TABLES - registered_tables
        assert not missing, f"Missing tables in Base.metadata: {missing}"
        assert self.EXPECTED_TABLES.issubset(registered_tables)

    def test_uuid_primary_keys_on_all_models(self):
        """Every table must have a primary key 'id' configured as Uuid."""
        for table_name in self.EXPECTED_TABLES:
            table = Base.metadata.tables[table_name]
            assert "id" in table.c, f"Table '{table_name}' is missing 'id' column"
            id_col = table.c["id"]
            assert id_col.primary_key, f"Column 'id' in table '{table_name}' must be primary key"
            assert not id_col.nullable, f"Column 'id' in table '{table_name}' must not be nullable"
            assert isinstance(id_col.type, Uuid), (
                f"Column 'id' in '{table_name}' must be Uuid, got {type(id_col.type)}"
            )

    def test_foreign_key_references_and_cascade_actions(self):
        """Verify FK target columns and cascade action rules across all domain models."""
        expected_fks = {
            ("operators", "user_id"): ("users.id", "CASCADE"),
            ("listings", "operator_id"): ("operators.id", "CASCADE"),
            ("listings", "destination_id"): ("destinations.id", "RESTRICT"),
            ("itineraries", "user_id"): ("users.id", "CASCADE"),
            ("itineraries", "destination_id"): ("destinations.id", "SET NULL"),
            ("itinerary_items", "itinerary_id"): ("itineraries.id", "CASCADE"),
            ("itinerary_items", "listing_id"): ("listings.id", "SET NULL"),
            ("bookings", "user_id"): ("users.id", "CASCADE"),
            ("bookings", "listing_id"): ("listings.id", "RESTRICT"),
            ("bookings", "itinerary_id"): ("itineraries.id", "SET NULL"),
            ("reviews", "user_id"): ("users.id", "CASCADE"),
            ("reviews", "listing_id"): ("listings.id", "CASCADE"),
            ("reviews", "booking_id"): ("bookings.id", "SET NULL"),
        }

        for (table_name, col_name), (target_col, on_delete) in expected_fks.items():
            table = Base.metadata.tables[table_name]
            assert col_name in table.c, f"Column '{col_name}' missing in table '{table_name}'"
            col = table.c[col_name]
            fks = list(col.foreign_keys)
            assert len(fks) == 1, (
                f"Expected exactly 1 FK on {table_name}.{col_name}, found {len(fks)}"
            )
            fk = fks[0]
            assert fk.target_fullname == target_col, (
                f"Expected FK {table_name}.{col_name} -> {target_col}, got {fk.target_fullname}"
            )
            assert (fk.ondelete or "").upper() == on_delete.upper(), (
                f"Expected ondelete='{on_delete}' on {table_name}.{col_name}, got '{fk.ondelete}'"
            )

    def test_check_constraints_defined(self):
        """Verify expected domain CheckConstraints exist on tables."""
        expected_constraints = {
            "listings": {"ck_listings_base_price", "ck_listings_rating_average"},
            "itineraries": {"ck_itineraries_dates"},
            "itinerary_items": {"ck_itinerary_items_day_number", "ck_itinerary_items_order_index"},
            "bookings": {"ck_bookings_dates", "ck_bookings_guests", "ck_bookings_price"},
            "reviews": {"ck_reviews_rating"},
        }
        for table_name, constraint_names in expected_constraints.items():
            table = Base.metadata.tables[table_name]
            registered_ck_names = {ck.name for ck in table.constraints if ck.name and ck.name.startswith("ck_")}
            missing = constraint_names - registered_ck_names
            assert not missing, f"Missing CheckConstraints on '{table_name}': {missing}"

    def test_in_memory_model_instantiation_and_graph_links(self):
        """Instantiate models in memory and assert relationship traversal works."""
        u_id = uuid.uuid4()
        user = User(
            id=u_id,
            email="traveler@example.com",
            hashed_password="secure_hashed_password_123",
            full_name="Jane Doe",
            role="operator",
            is_active=True,
        )
        assert user.id == u_id
        assert user.email == "traveler@example.com"
        assert user.role == "operator"

        operator = Operator(
            id=uuid.uuid4(),
            user_id=user.id,
            business_name="Alpine Adventures",
            business_type="agency",
            contact_email="contact@alpine.com",
            user=user,
        )
        assert operator.user == user
        assert user.operator == operator

        destination = Destination(
            id=uuid.uuid4(),
            name="Zermatt",
            slug="zermatt-switzerland",
            country="Switzerland",
            timezone="Europe/Zurich",
        )
        listing = Listing(
            id=uuid.uuid4(),
            operator_id=operator.id,
            destination_id=destination.id,
            title="Matterhorn Heli-Skiing",
            slug="matterhorn-heli-skiing",
            category="adventure",
            description="Exhilarating skiing on fresh powder",
            base_price=Decimal("450.00"),
            operator=operator,
            destination=destination,
        )
        assert listing.operator == operator
        assert listing.destination == destination
        assert listing in operator.listings
        assert listing in destination.listings

        itinerary = Itinerary(
            id=uuid.uuid4(),
            user_id=user.id,
            destination_id=destination.id,
            title="Winter Holiday 2026",
            start_date=date(2026, 12, 1),
            end_date=date(2026, 12, 7),
            user=user,
            destination=destination,
        )
        item = ItineraryItem(
            id=uuid.uuid4(),
            itinerary_id=itinerary.id,
            listing_id=listing.id,
            day_number=1,
            order_index=0,
            title="Morning Heli Flight",
            itinerary=itinerary,
            listing=listing,
        )
        assert item in itinerary.items
        assert item.itinerary == itinerary
        assert item in listing.itinerary_items

        booking = Booking(
            id=uuid.uuid4(),
            user_id=user.id,
            listing_id=listing.id,
            itinerary_id=itinerary.id,
            booking_reference="BK-2026-TEST-001",
            start_date=date(2026, 12, 2),
            end_date=date(2026, 12, 3),
            guests_count=2,
            total_price=Decimal("900.00"),
            user=user,
            listing=listing,
            itinerary=itinerary,
        )
        assert booking in user.bookings
        assert booking in listing.bookings
        assert booking in itinerary.bookings

        review = Review(
            id=uuid.uuid4(),
            user_id=user.id,
            listing_id=listing.id,
            booking_id=booking.id,
            rating=5,
            comment="Unbelievable experience!",
            user=user,
            listing=listing,
            booking=booking,
        )
        assert review in user.reviews
        assert review in listing.reviews
        assert booking.review == review

    def test_sqlite_in_memory_ddl_compilation(self):
        """
        Verify that all domain model DDL statements compile and execute cleanly
        against an in-memory SQLite engine without Postgres syntax errors.
        """
        engine = create_engine("sqlite:///:memory:", echo=False)
        try:
            Base.metadata.create_all(engine)
            with engine.connect() as conn:
                from sqlalchemy import inspect
                inspector = inspect(conn)
                tables = set(inspector.get_table_names())
                assert self.EXPECTED_TABLES.issubset(tables)
            Base.metadata.drop_all(engine)
        finally:
            engine.dispose()

    def test_session_persistence_populates_core_defaults(self):
        """
        Verify that when an instance without explicit id/is_active/role/created_at
        is persisted into a database session, SQLAlchemy evaluates and populates
        the Core defaults (id as UUID, is_active=True, role='tourist', created_at timestamp).
        """
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            user = User(
                email="default_test@example.com",
                hashed_password="hashed_pw_xyz",
            )
            # Before flush, in-memory uninitialized attributes evaluate to None
            assert user.id is None
            assert user.is_active is None

            session.add(user)
            session.commit()

            # After commit/flush, defaults must be populated
            assert isinstance(user.id, uuid.UUID)
            assert user.is_active is True
            assert user.role == "tourist"
            assert user.preferred_language == "en"
            assert user.created_at is not None
            assert user.updated_at is not None
        engine.dispose()

    def test_check_constraints_enforced_by_database(self):
        """Verify that CheckConstraints actively reject invalid values during session commit."""
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)

        # Pre-populate valid parent objects
        u_id = uuid.uuid4()
        op_id = uuid.uuid4()
        dest_id = uuid.uuid4()
        list_id = uuid.uuid4()

        with Session(engine) as session:
            u = User(id=u_id, email="rev_u@ex.com", hashed_password="pw")
            op = Operator(id=op_id, user_id=u_id, business_name="Op", contact_email="e@e.com")
            dest = Destination(id=dest_id, name="D", slug="d-1", country="C")
            list_obj = Listing(
                id=list_id,
                operator_id=op_id,
                destination_id=dest_id,
                title="L",
                slug="l-1",
                category="tour",
                description="desc",
                base_price=Decimal("10.00"),
            )
            session.add_all([u, op, dest, list_obj])
            session.commit()

        # 1. ck_reviews_rating (rating between 1 and 5)
        with Session(engine) as session:
            invalid_review = Review(
                id=uuid.uuid4(),
                user_id=u_id,
                listing_id=list_id,
                rating=6,  # Invalid: > 5
            )
            session.add(invalid_review)
            with pytest.raises(IntegrityError):
                session.commit()

        # 2. ck_listings_base_price (base_price >= 0)
        with Session(engine) as session:
            invalid_listing = Listing(
                id=uuid.uuid4(),
                operator_id=op_id,
                destination_id=dest_id,
                title="Negative Price Tour",
                slug="neg-price-tour",
                category="tour",
                description="desc",
                base_price=Decimal("-5.00"),  # Invalid
            )
            session.add(invalid_listing)
            with pytest.raises(IntegrityError):
                session.commit()

        # 3. ck_itineraries_dates (start_date <= end_date)
        with Session(engine) as session:
            invalid_itinerary = Itinerary(
                id=uuid.uuid4(),
                user_id=u_id,
                title="Backwards Travel",
                start_date=date(2026, 12, 10),
                end_date=date(2026, 12, 1),  # Invalid: start > end
            )
            session.add(invalid_itinerary)
            with pytest.raises(IntegrityError):
                session.commit()

        # 4. ck_bookings_guests (guests_count >= 1)
        with Session(engine) as session:
            invalid_booking = Booking(
                id=uuid.uuid4(),
                user_id=u_id,
                listing_id=list_id,
                booking_reference="BK-ZERO-GUEST",
                start_date=date(2026, 12, 1),
                end_date=date(2026, 12, 2),
                guests_count=0,  # Invalid: < 1
                total_price=Decimal("100.00"),
            )
            session.add(invalid_booking)
            with pytest.raises(IntegrityError):
                session.commit()

        engine.dispose()

    def test_unique_constraints_enforced_by_database(self):
        """Verify unique constraints reject duplicate entries."""
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)

        # Duplicate email
        with Session(engine) as session:
            u1 = User(id=uuid.uuid4(), email="duplicate@example.com", hashed_password="pw1")
            u2 = User(id=uuid.uuid4(), email="duplicate@example.com", hashed_password="pw2")
            session.add(u1)
            session.commit()
            session.add(u2)
            with pytest.raises(IntegrityError):
                session.commit()
            session.rollback()

        # Duplicate destination slug
        with Session(engine) as session:
            d1 = Destination(id=uuid.uuid4(), name="Dest1", slug="common-slug", country="C1")
            d2 = Destination(id=uuid.uuid4(), name="Dest2", slug="common-slug", country="C2")
            session.add(d1)
            session.commit()
            session.add(d2)
            with pytest.raises(IntegrityError):
                session.commit()
            session.rollback()

        engine.dispose()


# ============================================================================
# TIER D: ALEMBIC MIGRATION SCRIPT INTEGRITY
# ============================================================================
class TestAlembicMigrationScriptIntegrity:
    """Stress-test 001_initial_schema.py, upgrade/downgrade methods, and SQL generation."""

    MIGRATION_PATH = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "alembic",
            "versions",
            "001_initial_schema.py",
        )
    )

    def test_migration_file_exists(self):
        """001_initial_schema.py must exist at backend/alembic/versions/."""
        assert os.path.isfile(self.MIGRATION_PATH), (
            f"Migration file not found at: {self.MIGRATION_PATH}"
        )

    def test_migration_syntax_and_callable_hooks(self):
        """Migration file must load cleanly and export upgrade() and downgrade()."""
        spec = importlib.util.spec_from_file_location("migration_001", self.MIGRATION_PATH)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            pytest.fail(f"Failed to execute migration module: {e}")

        assert hasattr(module, "upgrade"), "Migration module missing 'upgrade' function"
        assert callable(module.upgrade), "'upgrade' must be callable"
        assert hasattr(module, "downgrade"), "Migration module missing 'downgrade' function"
        assert callable(module.downgrade), "'downgrade' must be callable"
        assert getattr(module, "revision") == "001_initial_schema"
        assert getattr(module, "down_revision") is None

    def test_migration_downgrade_topological_drop_order(self):
        """
        Verify that downgrade() drops tables in exact reverse dependency order
        to prevent foreign key violation errors during rollback.
        """
        with open(self.MIGRATION_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        parsed = ast.parse(content)
        downgrade_def = None
        for node in parsed.body:
            if isinstance(node, ast.FunctionDef) and node.name == "downgrade":
                downgrade_def = node
                break

        assert downgrade_def is not None, "Could not find downgrade() function in AST"

        dropped_tables: List[str] = []
        for stmt in downgrade_def.body:
            if (
                isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Call)
                and isinstance(stmt.value.func, ast.Attribute)
                and stmt.value.func.attr == "drop_table"
                and len(stmt.value.args) > 0
                and isinstance(stmt.value.args[0], ast.Constant)
            ):
                dropped_tables.append(stmt.value.args[0].value)

        expected_order = [
            "reviews",
            "bookings",
            "itinerary_items",
            "itineraries",
            "listings",
            "operators",
            "destinations",
            "users",
        ]
        assert dropped_tables == expected_order, (
            f"Downgrade drop order mismatch.\nExpected: {expected_order}\nGot: {dropped_tables}"
        )

    def test_migration_column_parity_with_domain_models(self):
        """
        Verify 100% column parity between 001_initial_schema.py and SQLAlchemy Base.metadata.
        Every column in declarative models must be declared in the migration table creation.
        """
        with open(self.MIGRATION_PATH, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())

        upgrade_func = next(
            n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "upgrade"
        )

        migration_tables: Dict[str, Set[str]] = {}
        for stmt in upgrade_func.body:
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                call = stmt.value
                if getattr(call.func, "attr", None) == "create_table":
                    tbl_name = call.args[0].value
                    cols = set()
                    for arg in call.args[1:]:
                        if isinstance(arg, ast.Call) and getattr(arg.func, "attr", None) == "Column":
                            cols.add(arg.args[0].value)
                    migration_tables[tbl_name] = cols

        for table_name in Base.metadata.tables.keys():
            assert table_name in migration_tables, f"Table {table_name} missing from migration"
            model_cols = set(Base.metadata.tables[table_name].columns.keys())
            mig_cols = migration_tables[table_name]
            diff = model_cols ^ mig_cols
            assert not diff, (
                f"Column mismatch on table '{table_name}':\n"
                f"In model only: {model_cols - mig_cols}\n"
                f"In migration only: {mig_cols - model_cols}"
            )

    def test_migration_offline_sql_generation(self):
        """
        Verify that Alembic generates offline PostgreSQL SQL for both
        'upgrade head' and 'downgrade base' without connecting to live DB.
        """
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        alembic_ini = os.path.join(backend_dir, "alembic.ini")

        # 1. Test upgrade offline SQL
        cmd_upgrade = [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            alembic_ini,
            "upgrade",
            "head",
            "--sql",
        ]
        res_up = subprocess.run(cmd_upgrade, cwd=backend_dir, capture_output=True, text=True)
        assert res_up.returncode == 0, f"Alembic upgrade --sql failed:\n{res_up.stderr}"
        sql_up = res_up.stdout
        for tbl in (
            "users",
            "destinations",
            "operators",
            "listings",
            "itineraries",
            "itinerary_items",
            "bookings",
            "reviews",
        ):
            assert f"CREATE TABLE {tbl}" in sql_up, f"CREATE TABLE {tbl} missing from offline SQL"

        # 2. Test downgrade offline SQL
        cmd_down = [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            alembic_ini,
            "downgrade",
            "001_initial_schema:base",
            "--sql",
        ]
        res_down = subprocess.run(cmd_down, cwd=backend_dir, capture_output=True, text=True)
        assert res_down.returncode == 0, f"Alembic downgrade --sql failed:\n{res_down.stderr}"
        sql_down = res_down.stdout
        for tbl in (
            "reviews",
            "bookings",
            "itinerary_items",
            "itineraries",
            "listings",
            "operators",
            "destinations",
            "users",
        ):
            assert f"DROP TABLE {tbl}" in sql_down, f"DROP TABLE {tbl} missing from downgrade offline SQL"

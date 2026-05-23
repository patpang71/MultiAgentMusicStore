"""
Database health check — verifies all Chinook tables exist and are queryable.

Can be run directly:
    python -m pytest dbscripts/tests/test_db_health.py -v

Or called as a function:
    from dbscripts.tests.test_db_health import check_db_health
    result = check_db_health()
"""

import json
import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()

EXPECTED_TABLES = [
    "Album",
    "Artist",
    "Customer",
    "Employee",
    "Genre",
    "Invoice",
    "InvoiceLine",
    "MediaType",
    "Playlist",
    "PlaylistTrack",
    "Track",
]


def _get_engine():
    url = os.environ.get("DATABASE_URL")
    if not url:
        host = os.environ["DB_HOST"]
        user = os.environ["DB_USER"]
        password = os.environ["DB_PASSWORD"]
        db = os.environ.get("DB_NAME", "Chinook_AutoIncrement")
        url = f"mysql+pymysql://{user}:{password}@{host}/{db}"
    return create_engine(url)


def check_db_health() -> str:
    """Verify that all Chinook tables exist and return row counts for each.

    Returns:
        JSON string with keys:
            status  — "healthy" or "unhealthy"
            tables  — dict of {table_name: row_count}
            missing — list of expected tables not found in the database
            errors  — list of error messages (empty when healthy)
    """
    result = {"status": "healthy", "tables": {}, "missing": [], "errors": []}

    try:
        engine = _get_engine()

        with engine.connect() as conn:
            inspector = inspect(engine)
            existing = {t.lower() for t in inspector.get_table_names()}

            for table in EXPECTED_TABLES:
                if table.lower() not in existing:
                    result["missing"].append(table)
                    result["errors"].append(f"Table '{table}' not found")
                    continue

                row = conn.execute(
                    text(f"SELECT COUNT(*) FROM `{table}`")  # noqa: S608
                ).scalar()
                result["tables"][table] = row

    except SQLAlchemyError as exc:
        result["errors"].append(str(exc))

    if result["missing"] or result["errors"]:
        result["status"] = "unhealthy"

    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# pytest tests — these run in the CodePipeline Test and DB_Health_Check stages
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def health():
    return json.loads(check_db_health())


def test_connection_succeeds(health):
    assert "errors" in health, "Health check did not return expected shape"
    connection_errors = [e for e in health["errors"] if "connection" in e.lower()
                         or "access denied" in e.lower()
                         or "can't connect" in e.lower()]
    assert not connection_errors, f"DB connection failed: {connection_errors}"


def test_no_missing_tables(health):
    assert health["missing"] == [], (
        f"Missing tables: {health['missing']}"
    )


def test_all_tables_have_rows(health):
    empty = [t for t, count in health["tables"].items() if count == 0]
    assert not empty, f"Tables with zero rows (seed may have failed): {empty}"


def test_status_is_healthy(health):
    assert health["status"] == "healthy", (
        f"DB health check unhealthy.\n{json.dumps(health, indent=2)}"
    )

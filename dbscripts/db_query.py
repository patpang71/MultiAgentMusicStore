import json
import os
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()


def _get_engine():
    url = os.environ.get("DATABASE_URL")
    if not url:
        host = os.environ["DB_HOST"]
        user = os.environ["DB_USER"]
        password = os.environ["DB_PASSWORD"]
        db = os.environ.get("DB_NAME", "Chinook_AutoIncrement")
        url = f"mysql+pymysql://{user}:{password}@{host}/{db}"
    return create_engine(url)


def _default_serializer(obj: Any) -> Any:
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def execute_query(sql: str, params: dict | None = None) -> str:
    """Execute a parameterised SQL query and return rows as a JSON string.

    Args:
        sql:    A SQL string, with named bind parameters written as :name.
                Example: "SELECT * FROM Track WHERE GenreId = :genre_id"
        params: Optional dict of parameter values, e.g. {"genre_id": 1}.

    Returns:
        A JSON string.  SELECT queries return a list of row objects.
        Non-SELECT statements (INSERT/UPDATE/DELETE) return a single object
        with "rowcount" and "lastrowid" keys.

    Raises:
        SQLAlchemyError: propagated on database errors.
    """
    engine = _get_engine()

    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})

        if result.returns_rows:
            keys = list(result.keys())
            rows = [dict(zip(keys, row)) for row in result.fetchall()]
            payload = rows
        else:
            conn.commit()
            payload = {"rowcount": result.rowcount, "lastrowid": result.lastrowid}

    return json.dumps(payload, default=_default_serializer)

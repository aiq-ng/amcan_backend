
import asyncpg
from typing import Optional, List, Any, Tuple
import os
from contextlib import asynccontextmanager

async def get_db_connection() -> asyncpg.Connection:
    """Establish a connection to the PostgreSQL database."""
    try:
        conn = await asyncpg.connect(
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            database=os.getenv("POSTGRES_DB"),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432")
        )
        return conn
    except Exception as e:
        raise ConnectionError(f"Failed to connect to database: {str(e)}")

@asynccontextmanager
async def db_connection():
    """Context manager for database connection."""
    conn = await get_db_connection()
    try:
        yield conn
    finally:
        await conn.close()

async def execute_query(conn: asyncpg.Connection, query: str, params: Tuple = ()) -> None:
    """Execute a raw SQL query that does not return results."""
    try:
        await conn.execute(query, *params)
    except Exception as e:
        raise RuntimeError(f"Query execution failed: {str(e)}")

async def fetch_one(conn: asyncpg.Connection, query: str, params: Tuple = ()) -> Optional[dict]:
    """Fetch a single row from a raw SQL query."""
    try:
        row = await conn.fetchrow(query, *params)
        return dict(row) if row else None
    except Exception as e:
        raise RuntimeError(f"Fetch one failed: {str(e)}")

async def fetch_all(conn: asyncpg.Connection, query: str, params: Tuple = ()) -> List[dict]:
    """Fetch all rows from a raw SQL query."""
    try:
        print(f"fetch_all params: {params} (type: {type(params)})")
        # Flatten params if it's a tuple/list of length 1 containing a tuple/list
        if len(params) == 1 and isinstance(params[0], (tuple, list)):
            params = params[0]
            print(f"fetch_all params flattened: {params}")
        rows = await conn.fetch(query, *params)
        return [dict(row) for row in rows]
    except Exception as e:
        raise RuntimeError(f"Fetch all failed: {str(e)}")

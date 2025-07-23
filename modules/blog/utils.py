import asyncpg
from typing import Optional, List, Any, Tuple
import os
from contextlib import asynccontextmanager
import cloudinary
import cloudinary.uploader

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

async def get_db_connection() -> asyncpg.Connection:
    """Establish a connection to the PostgreSQL database."""
    try:
        conn = await asyncpg.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_DB"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
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
        rows = await conn.fetch(query, *params)
        return [dict(row) for row in rows]
    except Exception as e:
        raise RuntimeError(f"Fetch all failed: {str(e)}")

async def upload_to_cloudinary(file_path: str, resource_type: str) -> str:
    """Upload file to Cloudinary and return public URL."""
    try:
        if resource_type == "audio":
            resource_type = "video"
        result = cloudinary.uploader.upload(file_path, resource_type=resource_type)
        return result['secure_url']
    except Exception as e:
        raise RuntimeError(f"Cloudinary upload failed: {str(e)}")
    
async def upload_image(image_file, folder="podcast_images"):

        try:
            # Upload the image to Cloudinary
            response = cloudinary.uploader.upload(
                image_file,
                resource_type="image",  # Specify image type
                folder="amcan_thumbnails",          # Organize in a folder
                use_filename=True,      # Use original filename
                unique_filename=False   # Avoid appending random strings to filename
            )
            return response
        except cloudinary.exceptions.Error as e:
            raise Exception(f"Cloudinary upload failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")

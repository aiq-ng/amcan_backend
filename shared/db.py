import asyncpg
from typing import Optional
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "password")
        db_name = os.getenv("DB_NAME", "amcan_db_lgzh")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = int(os.getenv("DB_PORT", 5432))

        print(f"[DB] Attempting connection with user='{db_user}', host='{db_host}', port={db_port}, db='{db_name}'")
        try:
            self.pool = await asyncpg.create_pool(
                user=db_user,
                password=db_password,
                database=db_name,
                host=db_host,
                port=db_port
            )
            print("[DB] Successfully connected to the database.")
        except Exception as e:
            print(f"[DB] Failed to connect: {e}")
            raise

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

    @asynccontextmanager
    async def get_connection(self):
        if not self.pool:
            raise Exception("Database not initialized")
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                yield connection

db = Database()

async def init_db():
    await db.connect()
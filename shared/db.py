import asyncpg
from typing import Optional
from contextlib import asynccontextmanager

class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            user="postgres",
            password="password",
            database="amcan_db",
            host="localhost",
            port=5432
        )

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
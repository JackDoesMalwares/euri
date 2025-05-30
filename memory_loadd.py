# memory_loadd.py

import aiosqlite

DB_FILE = "server_memory.db"

async def initialize_memory():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                guild_id TEXT PRIMARY KEY,
                data TEXT
            )
        """)
        await db.commit()

async def load_memory(guild_id: int) -> str:
    await initialize_memory()
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT data FROM memory WHERE guild_id = ?", (str(guild_id),)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else ""

async def save_memory(guild_id: int, data: str):
    await initialize_memory()
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            INSERT INTO memory (guild_id, data) VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET data = excluded.data
        """, (str(guild_id), data))
        await db.commit()

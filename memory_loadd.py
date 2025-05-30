# memory_loadd.py

import aiosqlite
import asyncio

DB_FILE = "server_memory.db"
db = None  # Global DB connection

async def initialize_memory():
    global db
    if db is None:
        db = await aiosqlite.connect(DB_FILE)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                guild_id TEXT PRIMARY KEY,
                data TEXT
            )
        """)
        await db.commit()

async def load_memory(guild_id: int) -> str:
    try:
        async with db.execute("SELECT data FROM memory WHERE guild_id = ?", (str(guild_id),)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else ""
    except Exception as e:
        print(f"[ERROR] load_memory failed: {e}")
        return ""

async def save_memory(guild_id: int, data: str):
    try:
        await db.execute("""
            INSERT INTO memory (guild_id, data) VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET data = excluded.data
        """, (str(guild_id), data))
        await db.commit()
    except Exception as e:
        print(f"[ERROR] save_memory failed: {e}")

async def close_db():
    if db:
        await db.close()

# Example usage in your bot startup:
# await initialize_memory()

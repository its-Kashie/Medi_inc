#memory_session.py
import sqlite3

import asyncio
from datetime import datetime

class SQLiteSession:
    def __init__(self, session_id: str, db_path: str = "memory.db"):
        self.session_id = session_id
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()

    # ✅ Save message
    def append_message(self, role: str, content: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO memory (session_id, role, content, timestamp)
            VALUES (?, ?, ?, ?)
        """, (self.session_id, role, content, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()

    # ✅ Get last N messages
    def get_history(self, limit: int = 10):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role, content FROM memory
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (self.session_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

    # ✅ Async helper methods for demo scripts
    async def add_items(self, items):
        for item in items:
            self.append_message(item["role"], item["content"])

    async def get_items(self, limit: int = 50):
        return self.get_history(limit=limit)

    async def pop_item(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, role, content FROM memory
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT 1
        """, (self.session_id,))
        row = cursor.fetchone()
        if row:
            cursor.execute("DELETE FROM memory WHERE id = ?", (row[0],))
            conn.commit()
        conn.close()
        if row:
            return {"role": row[1], "content": row[2]}
        return None

    async def clear_session(self):
        self.clear()

    def clear(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memory WHERE session_id = ?", (self.session_id,))
        conn.commit()
        conn.close()

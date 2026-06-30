import json
import sqlite3
from datetime import datetime, timezone


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SessionService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get_context(self, session_id: str) -> dict:
        row = self.conn.execute(
            "SELECT context_json FROM sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if row is None:
            return {}
        return json.loads(row["context_json"])

    def save_context(self, session_id: str, context: dict) -> None:
        existing = self.get_context(session_id)
        existing.update(context)
        self.conn.execute(
            """
            INSERT INTO sessions (session_id, context_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
              context_json = excluded.context_json,
              updated_at = excluded.updated_at
            """,
            (session_id, json.dumps(existing, ensure_ascii=False), utc_now()),
        )
        self.conn.commit()
import sqlite3
from typing import List, Optional
from app.models.user import User
from app.repositories.db import get_db


class UserRepository:
    def __init__(self, conn: Optional[sqlite3.Connection] = None):
        self.conn = conn

    def _get_conn(self) -> sqlite3.Connection:
        if self.conn is not None:
            return self.conn
        return get_db()

    def _row_to_user(self, row: sqlite3.Row) -> User:
        return User(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            role=row["role"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
        )

    def create(
        self, username: str, password_hash: str, role: str = "student", is_active: bool = True
    ) -> User:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash, role, is_active) VALUES (?, ?, ?, ?)",
            (username.strip(), password_hash, role, 1 if is_active else 0),
        )
        conn.commit()
        user_id = cursor.lastrowid
        return self.get_by_id(user_id)

    def get_by_id(self, user_id: int) -> Optional[User]:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return None
        return self._row_to_user(row)

    def get_by_username(self, username: str) -> Optional[User]:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username.strip(),)
        ).fetchone()
        if not row:
            return None
        return self._row_to_user(row)

    def list_all(self) -> List[User]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM users ORDER BY id ASC").fetchall()
        return [self._row_to_user(r) for r in rows]

    def update_status(self, user_id: int, is_active: bool) -> bool:
        conn = self._get_conn()
        cursor = conn.execute(
            "UPDATE users SET is_active = ? WHERE id = ?",
            (1 if is_active else 0, user_id),
        )
        conn.commit()
        return cursor.rowcount > 0

    def count(self) -> int:
        conn = self._get_conn()
        row = conn.execute("SELECT COUNT(*) AS cnt FROM users").fetchone()
        return row["cnt"] if row else 0

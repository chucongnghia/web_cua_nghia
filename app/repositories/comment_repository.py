import sqlite3
from typing import List, Optional
from app.models.comment import Comment
from app.repositories.db import get_db


class CommentRepository:
    def __init__(self, conn: Optional[sqlite3.Connection] = None):
        self.conn = conn

    def _get_conn(self) -> sqlite3.Connection:
        if self.conn is not None:
            return self.conn
        return get_db()

    def _row_to_comment(self, row: sqlite3.Row) -> Comment:
        author_username = (
            row["author_username"] if "author_username" in row.keys() else ""
        )
        return Comment(
            id=row["id"],
            document_id=row["document_id"],
            user_id=row["user_id"],
            content=row["content"],
            created_at=row["created_at"],
            author_username=author_username,
        )

    def create(self, document_id: int, user_id: int, content: str) -> Comment:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO comments (document_id, user_id, content)
            VALUES (?, ?, ?)
            """,
            (document_id, user_id, content.strip()),
        )
        conn.commit()
        comment_id = cursor.lastrowid
        return self.get_by_id(comment_id)

    def get_by_id(self, comment_id: int) -> Optional[Comment]:
        conn = self._get_conn()
        row = conn.execute(
            """
            SELECT c.*, u.username AS author_username
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.id = ?
            """,
            (comment_id,),
        ).fetchone()
        if not row:
            return None
        return self._row_to_comment(row)

    def list_by_document(self, document_id: int) -> List[Comment]:
        conn = self._get_conn()
        rows = conn.execute(
            """
            SELECT c.*, u.username AS author_username
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.document_id = ?
            ORDER BY c.created_at ASC
            """,
            (document_id,),
        ).fetchall()
        return [self._row_to_comment(r) for r in rows]

    def delete(self, comment_id: int) -> bool:
        conn = self._get_conn()
        cursor = conn.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
        conn.commit()
        return cursor.rowcount > 0

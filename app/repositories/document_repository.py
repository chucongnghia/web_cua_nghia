import sqlite3
from typing import List, Optional
from app.models.document import Document
from app.repositories.db import get_db


class DocumentRepository:
    def __init__(self, conn: Optional[sqlite3.Connection] = None):
        self.conn = conn

    def _get_conn(self) -> sqlite3.Connection:
        if self.conn is not None:
            return self.conn
        return get_db()

    def _row_to_document(self, row: sqlite3.Row) -> Document:
        owner_username = row["owner_username"] if "owner_username" in row.keys() else ""
        return Document(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            subject=row["subject"],
            is_public=bool(row["is_public"]),
            status=row["status"],
            filename=row["filename"],
            original_filename=row["original_filename"],
            file_size=row["file_size"],
            owner_id=row["owner_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            owner_username=owner_username,
        )

    def create(
        self,
        title: str,
        description: str,
        subject: str,
        is_public: bool,
        filename: str,
        original_filename: str,
        file_size: int,
        owner_id: int,
        status: str = "approved",
    ) -> Document:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO documents (
                title, description, subject, is_public, status,
                filename, original_filename, file_size, owner_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title.strip(),
                description.strip(),
                subject.strip(),
                1 if is_public else 0,
                status,
                filename,
                original_filename,
                file_size,
                owner_id,
            ),
        )
        conn.commit()
        doc_id = cursor.lastrowid
        return self.get_by_id(doc_id)

    def get_by_id(self, doc_id: int) -> Optional[Document]:
        conn = self._get_conn()
        row = conn.execute(
            """
            SELECT d.*, u.username AS owner_username
            FROM documents d
            JOIN users u ON d.owner_id = u.id
            WHERE d.id = ?
            """,
            (doc_id,),
        ).fetchone()
        if not row:
            return None
        return self._row_to_document(row)

    def get_by_filename(self, filename: str) -> Optional[Document]:
        conn = self._get_conn()
        row = conn.execute(
            """
            SELECT d.*, u.username AS owner_username
            FROM documents d
            JOIN users u ON d.owner_id = u.id
            WHERE d.filename = ?
            """,
            (filename,),
        ).fetchone()
        if not row:
            return None
        return self._row_to_document(row)

    def list_public(self) -> List[Document]:
        conn = self._get_conn()
        rows = conn.execute(
            """
            SELECT d.*, u.username AS owner_username
            FROM documents d
            JOIN users u ON d.owner_id = u.id
            WHERE d.is_public = 1
            ORDER BY d.created_at DESC
            """
        ).fetchall()
        return [self._row_to_document(r) for r in rows]

    def list_by_owner(self, owner_id: int) -> List[Document]:
        conn = self._get_conn()
        rows = conn.execute(
            """
            SELECT d.*, u.username AS owner_username
            FROM documents d
            JOIN users u ON d.owner_id = u.id
            WHERE d.owner_id = ?
            ORDER BY d.created_at DESC
            """,
            (owner_id,),
        ).fetchall()
        return [self._row_to_document(r) for r in rows]

    def search(
        self,
        keyword: Optional[str] = None,
        subject: Optional[str] = None,
        user_id: Optional[int] = None,
        is_admin: bool = False,
    ) -> List[Document]:
        conn = self._get_conn()
        conditions = []
        params = []

        # Access scope condition
        if is_admin:
            pass  # Admin can view all documents
        elif user_id is not None:
            conditions.append("(d.is_public = 1 OR d.owner_id = ?)")
            params.append(user_id)
        else:
            conditions.append("d.is_public = 1")

        # Keyword condition (title, subject, description)
        if keyword and keyword.strip():
            kw_pattern = f"%{keyword.strip()}%"
            conditions.append(
                "(py_lower(d.title) LIKE py_lower(?) OR py_lower(d.subject) LIKE py_lower(?) OR py_lower(d.description) LIKE py_lower(?))"
            )
            params.extend([kw_pattern, kw_pattern, kw_pattern])

        # Subject filter
        if subject and subject.strip():
            conditions.append("d.subject = ?")
            params.append(subject.strip())

        query = """
            SELECT d.*, u.username AS owner_username
            FROM documents d
            JOIN users u ON d.owner_id = u.id
        """
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY d.created_at DESC"

        rows = conn.execute(query, params).fetchall()
        return [self._row_to_document(r) for r in rows]

    def update(
        self,
        doc_id: int,
        title: str,
        description: str,
        subject: str,
        is_public: bool,
        filename: Optional[str] = None,
        original_filename: Optional[str] = None,
        file_size: Optional[int] = None,
    ) -> bool:
        conn = self._get_conn()
        if filename is not None:
            cursor = conn.execute(
                """
                UPDATE documents
                SET title = ?, description = ?, subject = ?, is_public = ?,
                    filename = ?, original_filename = ?, file_size = ?,
                    updated_at = datetime('now', 'localtime')
                WHERE id = ?
                """,
                (
                    title.strip(),
                    description.strip(),
                    subject.strip(),
                    1 if is_public else 0,
                    filename,
                    original_filename,
                    file_size,
                    doc_id,
                ),
            )
        else:
            cursor = conn.execute(
                """
                UPDATE documents
                SET title = ?, description = ?, subject = ?, is_public = ?,
                    updated_at = datetime('now', 'localtime')
                WHERE id = ?
                """,
                (
                    title.strip(),
                    description.strip(),
                    subject.strip(),
                    1 if is_public else 0,
                    doc_id,
                ),
            )
        conn.commit()
        return cursor.rowcount > 0

    def update_status(self, doc_id: int, status: str) -> bool:
        conn = self._get_conn()
        cursor = conn.execute(
            """
            UPDATE documents
            SET status = ?, updated_at = datetime('now', 'localtime')
            WHERE id = ?
            """,
            (status, doc_id),
        )
        conn.commit()
        return cursor.rowcount > 0

    def delete(self, doc_id: int) -> bool:
        conn = self._get_conn()
        cursor = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
        return cursor.rowcount > 0

    def get_distinct_subjects(self) -> List[str]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT DISTINCT subject FROM documents WHERE subject != '' ORDER BY subject ASC"
        ).fetchall()
        return [r["subject"] for r in rows]

    def count_by_owner(self, owner_id: int) -> int:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM documents WHERE owner_id = ?", (owner_id,)
        ).fetchone()
        return row["cnt"] if row else 0

    def count_all(self) -> int:
        conn = self._get_conn()
        row = conn.execute("SELECT COUNT(*) AS cnt FROM documents").fetchone()
        return row["cnt"] if row else 0

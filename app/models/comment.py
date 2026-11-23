from dataclasses import dataclass


@dataclass
class Comment:
    id: int
    document_id: int
    user_id: int
    content: str
    created_at: str
    author_username: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "document_id": self.document_id,
            "user_id": self.user_id,
            "content": self.content,
            "created_at": self.created_at,
            "author_username": self.author_username,
        }

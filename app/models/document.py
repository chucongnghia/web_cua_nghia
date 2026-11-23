from dataclasses import dataclass


@dataclass
class Document:
    id: int
    title: str
    description: str
    subject: str
    is_public: bool
    status: str
    filename: str
    original_filename: str
    file_size: int
    owner_id: int
    created_at: str
    updated_at: str
    owner_username: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "subject": self.subject,
            "is_public": self.is_public,
            "status": self.status,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "owner_id": self.owner_id,
            "owner_username": self.owner_username,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

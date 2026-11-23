import os
import uuid
from pathlib import Path
from typing import Optional, Set, Tuple
from werkzeug.utils import secure_filename


class StorageRepository:
    def __init__(
        self, upload_folder: str, allowed_extensions: Optional[Set[str]] = None
    ):
        self.upload_folder = os.path.abspath(upload_folder)
        self.allowed_extensions = (
            {ext.lower().lstrip(".") for ext in allowed_extensions}
            if allowed_extensions
            else {"pdf", "docx", "txt"}
        )
        os.makedirs(self.upload_folder, exist_ok=True)

    def is_allowed_file(self, filename: str) -> bool:
        if not filename or "." not in filename:
            return False
        ext = filename.rsplit(".", 1)[1].lower()
        return ext in self.allowed_extensions

    def save_file(self, file_storage) -> Tuple[str, str, int]:
        """
        Saves uploaded file to disk with a secure randomized filename.
        Returns: (saved_filename, original_filename, file_size)
        """
        raw_original = file_storage.filename or "file"
        safe_original = secure_filename(raw_original)
        if not safe_original:
            safe_original = "document"

        ext = ""
        if "." in safe_original:
            ext = "." + safe_original.rsplit(".", 1)[1].lower()

        unique_prefix = uuid.uuid4().hex[:12]
        saved_filename = f"{unique_prefix}_{safe_original}"
        dest_path = os.path.join(self.upload_folder, saved_filename)

        file_storage.seek(0)
        file_storage.save(dest_path)
        file_size = os.path.getsize(dest_path)

        return saved_filename, raw_original, file_size

    def save_raw_content(
        self, filename: str, content: bytes
    ) -> Tuple[str, str, int]:
        """
        Helper for seeds/tests to create a file on disk directly.
        """
        safe_original = secure_filename(filename) or "sample.txt"
        unique_prefix = uuid.uuid4().hex[:12]
        saved_filename = f"{unique_prefix}_{safe_original}"
        dest_path = os.path.join(self.upload_folder, saved_filename)

        with open(dest_path, "wb") as f:
            f.write(content)

        return saved_filename, safe_original, len(content)

    def get_file_path(self, filename: str) -> Optional[str]:
        """
        Resolves safe file path inside upload_folder.
        Prevents directory traversal (e.g., ../../etc/passwd).
        """
        if not filename:
            return None

        # Sanitize filename to basename only
        clean_name = os.path.basename(filename)
        candidate = os.path.abspath(os.path.join(self.upload_folder, clean_name))

        # Check path boundary
        if not candidate.startswith(self.upload_folder):
            return None

        if os.path.isfile(candidate):
            return candidate
        return None

    def delete_file(self, filename: str) -> bool:
        file_path = self.get_file_path(filename)
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True
            except OSError:
                return False
        return False

    def file_exists(self, filename: str) -> bool:
        path = self.get_file_path(filename)
        return path is not None and os.path.isfile(path)

from typing import List, Optional, Tuple
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.storage_repository import StorageRepository
from app.services.logger_service import log_activity


class AdminService:
    def __init__(
        self,
        user_repo: Optional[UserRepository] = None,
        document_repo: Optional[DocumentRepository] = None,
        storage_repo: Optional[StorageRepository] = None,
    ):
        self.user_repo = user_repo or UserRepository()
        self.document_repo = document_repo or DocumentRepository()
        self.storage_repo = storage_repo

    def list_all_users(
        self, current_user: User
    ) -> Tuple[Optional[List[User]], Optional[str]]:
        if not current_user or not current_user.is_admin():
            return None, "Bạn không có quyền truy cập trang quản trị."
        users = self.user_repo.list_all()
        return users, None

    def toggle_user_status(
        self, current_user: User, target_user_id: int
    ) -> Tuple[bool, Optional[str]]:
        if not current_user or not current_user.is_admin():
            return False, "Chỉ quản trị viên mới có quyền thay đổi trạng thái người dùng."

        if current_user.id == target_user_id:
            return False, "Quản trị viên không thể tự khóa tài khoản của chính mình."

        target_user = self.user_repo.get_by_id(target_user_id)
        if not target_user:
            return False, "Không tìm thấy người dùng."

        new_status = not target_user.is_active
        self.user_repo.update_status(target_user.id, new_status)

        status_str = "mở khóa" if new_status else "khóa"
        log_activity(
            action="ADMIN_TOGGLE_USER_STATUS",
            username=current_user.username,
            details=f"Admin đã {status_str} tài khoản '{target_user.username}' (ID={target_user.id})",
        )
        return True, None

    def approve_document(
        self, current_user: User, doc_id: int
    ) -> Tuple[bool, Optional[str]]:
        if not current_user or not current_user.is_admin():
            return False, "Chỉ quản trị viên mới có quyền duyệt tài liệu."

        doc = self.document_repo.get_by_id(doc_id)
        if not doc:
            return False, "Không tìm thấy tài liệu cần duyệt."

        self.document_repo.update_status(doc.id, "approved")
        log_activity(
            action="ADMIN_APPROVE_DOCUMENT",
            username=current_user.username,
            details=f"Admin đã duyệt tài liệu ID={doc.id}, Tiêu đề='{doc.title}'",
        )
        return True, None

    def delete_any_document(
        self, current_user: User, doc_id: int
    ) -> Tuple[bool, Optional[str]]:
        if not current_user or not current_user.is_admin():
            return False, "Chỉ quản trị viên mới có quyền xóa tài liệu này."

        doc = self.document_repo.get_by_id(doc_id)
        if not doc:
            return False, "Không tìm thấy tài liệu cần xóa."

        if self.storage_repo:
            self.storage_repo.delete_file(doc.filename)

        self.document_repo.delete(doc.id)
        log_activity(
            action="ADMIN_DELETE_DOCUMENT",
            username=current_user.username,
            details=f"Admin xóa tài liệu ID={doc.id}, Tiêu đề='{doc.title}'",
        )
        return True, None

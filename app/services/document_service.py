from typing import List, Optional, Tuple
from app.models.document import Document
from app.models.comment import Comment
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.repositories.storage_repository import StorageRepository
from app.repositories.comment_repository import CommentRepository
from app.services.logger_service import log_activity


class DocumentService:
    def __init__(
        self,
        document_repo: Optional[DocumentRepository] = None,
        storage_repo: Optional[StorageRepository] = None,
        comment_repo: Optional[CommentRepository] = None,
    ):
        self.document_repo = document_repo or DocumentRepository()
        self.storage_repo = storage_repo
        self.comment_repo = comment_repo or CommentRepository()

    def create_document(
        self,
        title: str,
        description: str,
        subject: str,
        is_public: bool,
        file_storage,
        current_user: User,
    ) -> Tuple[Optional[Document], Optional[str]]:
        if not current_user:
            return None, "Bạn cần đăng nhập để tải lên tài liệu."

        title = (title or "").strip()
        subject = (subject or "").strip()
        description = (description or "").strip()

        if not title:
            return None, "Tiêu đề tài liệu không được để trống."
        if len(title) > 200:
            return None, "Tiêu đề không được vượt quá 200 ký tự."

        if not subject:
            return None, "Môn học không được để trống."
        if len(subject) > 100:
            return None, "Tên môn học không được vượt quá 100 ký tự."

        if not file_storage or not file_storage.filename:
            return None, "Vui lòng chọn tệp đính kèm."

        if not self.storage_repo.is_allowed_file(file_storage.filename):
            return (
                None,
                f"Định dạng tệp không được hỗ trợ. Chỉ chấp nhận các định dạng: {', '.join(self.storage_repo.allowed_extensions)}",
            )

        saved_filename, orig_filename, file_size = self.storage_repo.save_file(
            file_storage
        )

        doc = self.document_repo.create(
            title=title,
            description=description,
            subject=subject,
            is_public=is_public,
            filename=saved_filename,
            original_filename=orig_filename,
            file_size=file_size,
            owner_id=current_user.id,
            status="approved",
        )

        log_activity(
            action="DOCUMENT_UPLOAD",
            username=current_user.username,
            details=f"Tải lên tài liệu ID={doc.id}, Tiêu đề='{doc.title}', Tệp='{orig_filename}' ({file_size} bytes)",
        )
        return doc, None

    def update_document(
        self,
        doc_id: int,
        title: str,
        description: str,
        subject: str,
        is_public: bool,
        file_storage,
        current_user: User,
    ) -> Tuple[Optional[Document], Optional[str]]:
        if not current_user:
            return None, "Bạn cần đăng nhập để thực hiện thao tác này."

        doc = self.document_repo.get_by_id(doc_id)
        if not doc:
            return None, "Không tìm thấy tài liệu yêu cầu."

        # Resource permission check (V4 & V5)
        if not current_user.is_admin() and doc.owner_id != current_user.id:
            log_activity(
                action="UNAUTHORIZED_EDIT_ATTEMPT",
                username=current_user.username,
                details=f"Cố gắng chỉnh sửa tài liệu ID={doc.id} của người dùng khác",
                level="WARNING",
            )
            return None, "Bạn không có quyền chỉnh sửa tài liệu này."

        title = (title or "").strip()
        subject = (subject or "").strip()
        description = (description or "").strip()

        if not title:
            return None, "Tiêu đề tài liệu không được để trống."
        if not subject:
            return None, "Môn học không được để trống."

        new_filename = None
        new_orig_name = None
        new_file_size = None

        if file_storage and file_storage.filename:
            if not self.storage_repo.is_allowed_file(file_storage.filename):
                return (
                    None,
                    f"Định dạng tệp không được hỗ trợ ({', '.join(self.storage_repo.allowed_extensions)}).",
                )
            new_filename, new_orig_name, new_file_size = self.storage_repo.save_file(
                file_storage
            )
            # Remove old file from disk
            self.storage_repo.delete_file(doc.filename)

        self.document_repo.update(
            doc_id=doc.id,
            title=title,
            description=description,
            subject=subject,
            is_public=is_public,
            filename=new_filename,
            original_filename=new_orig_name,
            file_size=new_file_size,
        )

        updated_doc = self.document_repo.get_by_id(doc.id)
        log_activity(
            action="DOCUMENT_UPDATE",
            username=current_user.username,
            details=f"Cập nhật tài liệu ID={doc.id}, Tiêu đề='{updated_doc.title}'",
        )
        return updated_doc, None

    def delete_document(
        self, doc_id: int, current_user: User
    ) -> Tuple[bool, Optional[str]]:
        if not current_user:
            return False, "Bạn cần đăng nhập để xóa tài liệu."

        doc = self.document_repo.get_by_id(doc_id)
        if not doc:
            return False, "Không tìm thấy tài liệu cần xóa."

        # Permission check: must be owner or admin
        if not current_user.is_admin() and doc.owner_id != current_user.id:
            log_activity(
                action="UNAUTHORIZED_DELETE_ATTEMPT",
                username=current_user.username,
                details=f"Cố gắng xóa tài liệu ID={doc.id} trái phép",
                level="WARNING",
            )
            return False, "Bạn không có quyền xóa tài liệu này."

        # Delete file from storage
        self.storage_repo.delete_file(doc.filename)
        # Delete from DB (foreign keys cascade comments)
        self.document_repo.delete(doc.id)

        log_activity(
            action="DOCUMENT_DELETE",
            username=current_user.username,
            details=f"Xóa tài liệu ID={doc.id}, Tiêu đề='{doc.title}'",
        )
        return True, None

    def get_document_for_view(
        self, doc_id: int, current_user: Optional[User]
    ) -> Tuple[Optional[Document], Optional[str]]:
        doc = self.document_repo.get_by_id(doc_id)
        if not doc:
            return None, "Tài liệu không tồn tại."

        # If private, only owner or admin can view
        if not doc.is_public:
            if not current_user:
                return None, "Tài liệu này ở chế độ riêng tư. Bạn cần đăng nhập."
            if not current_user.is_admin() and doc.owner_id != current_user.id:
                return None, "Bạn không có quyền truy cập tài liệu riêng tư này."

        return doc, None

    def check_download_permission(
        self, doc_id_or_filename: str, current_user: Optional[User]
    ) -> Tuple[Optional[Document], Optional[str], Optional[str]]:
        """
        Resolves doc by integer ID or by filename.
        Returns (document, absolute_file_path, error_message).
        """
        doc = None
        if str(doc_id_or_filename).isdigit():
            doc = self.document_repo.get_by_id(int(doc_id_or_filename))
        if not doc:
            doc = self.document_repo.get_by_filename(str(doc_id_or_filename))

        if not doc:
            return None, None, "Không tìm thấy tài liệu tương ứng."

        # Permission check
        if not doc.is_public:
            if not current_user:
                return None, None, "Tài liệu này ở chế độ riêng tư. Vui lòng đăng nhập."
            if not current_user.is_admin() and doc.owner_id != current_user.id:
                log_activity(
                    action="UNAUTHORIZED_DOWNLOAD_ATTEMPT",
                    username=current_user.username,
                    details=f"Cố gắng tải tệp của tài liệu riêng tư ID={doc.id}",
                    level="WARNING",
                )
                return None, None, "Bạn không có quyền tải tệp đính kèm này."

        file_path = self.storage_repo.get_file_path(doc.filename)
        if not file_path:
            return None, None, "Tệp đính kèm không tồn tại trên hệ thống lưu trữ."

        username = current_user.username if current_user else "anonymous"
        log_activity(
            action="DOCUMENT_DOWNLOAD",
            username=username,
            details=f"Tải xuống tệp '{doc.original_filename}' của tài liệu ID={doc.id}",
        )
        return doc, file_path, None

    def search_documents(
        self,
        keyword: Optional[str] = None,
        subject: Optional[str] = None,
        current_user: Optional[User] = None,
    ) -> List[Document]:
        user_id = current_user.id if current_user else None
        is_admin = current_user.is_admin() if current_user else False
        return self.document_repo.search(
            keyword=keyword, subject=subject, user_id=user_id, is_admin=is_admin
        )

    def list_my_documents(self, current_user: User) -> List[Document]:
        if not current_user:
            return []
        return self.document_repo.list_by_owner(current_user.id)

    def get_subjects(self) -> List[str]:
        return self.document_repo.get_distinct_subjects()

    def add_comment(
        self, doc_id: int, current_user: User, content: str
    ) -> Tuple[Optional[Comment], Optional[str]]:
        if not current_user:
            return None, "Bạn cần đăng nhập để bình luận."

        doc, err = self.get_document_for_view(doc_id, current_user)
        if err or not doc:
            return None, err or "Không có quyền thêm bình luận vào tài liệu này."

        content = (content or "").strip()
        if not content:
            return None, "Nội dung bình luận không được để trống."
        if len(content) > 1000:
            return None, "Nội dung bình luận không được vượt quá 1000 ký tự."

        comment = self.comment_repo.create(
            document_id=doc.id, user_id=current_user.id, content=content
        )
        return comment, None

    def get_comments(self, doc_id: int) -> List[Comment]:
        return self.comment_repo.list_by_document(doc_id)

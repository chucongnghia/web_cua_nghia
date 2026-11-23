import io
import pytest
from werkzeug.datastructures import FileStorage
from app.services.document_service import DocumentService
from app.services.auth_service import AuthService
from app.services.admin_service import AdminService


def create_file_storage(name: str, content: bytes = b"Test file content"):
    return FileStorage(stream=io.BytesIO(content), filename=name)


def test_document_lifecycle_and_permissions(repos):
    auth_service = AuthService(repos["user_repo"])
    doc_service = DocumentService(
        document_repo=repos["doc_repo"],
        storage_repo=repos["storage_repo"],
        comment_repo=repos["comment_repo"],
    )
    admin_service = AdminService(
        user_repo=repos["user_repo"],
        document_repo=repos["doc_repo"],
        storage_repo=repos["storage_repo"],
    )

    # Setup 3 users: admin, student1, student2
    admin_user, _ = auth_service.register("admin_user", "Admin123", "admin")
    student1, _ = auth_service.register("student_one", "Student123", "student")
    student2, _ = auth_service.register("student_two", "Student123", "student")

    # 1. Create document with invalid file extension -> should fail
    bad_file = create_file_storage("hack.exe", b"malicious binary")
    doc_bad, err = doc_service.create_document(
        title="Bad Doc",
        description="",
        subject="IT",
        is_public=True,
        file_storage=bad_file,
        current_user=student1,
    )
    assert doc_bad is None
    assert "Định dạng tệp không được hỗ trợ" in err

    # 2. Student 1 creates a private document with valid PDF
    pdf_file = create_file_storage("exam_review.pdf", b"%PDF-1.4 sample content")
    doc_priv, err = doc_service.create_document(
        title="Đề ôn tập riêng tư",
        description="Chỉ mình tôi xem",
        subject="Toán học",
        is_public=False,
        file_storage=pdf_file,
        current_user=student1,
    )
    assert err is None
    assert doc_priv is not None
    assert doc_priv.is_public is False

    # 3. View permission check:
    # Student 1 (owner) can view
    d1, err = doc_service.get_document_for_view(doc_priv.id, student1)
    assert d1 is not None and err is None

    # Admin can view
    d_admin, err = doc_service.get_document_for_view(doc_priv.id, admin_user)
    assert d_admin is not None and err is None

    # Student 2 (stranger) CANNOT view private doc
    d2, err = doc_service.get_document_for_view(doc_priv.id, student2)
    assert d2 is None
    assert "không có quyền truy cập" in err

    # Anonymous CANNOT view private doc
    d_anon, err = doc_service.get_document_for_view(doc_priv.id, None)
    assert d_anon is None
    assert "Bạn cần đăng nhập" in err

    # 4. Download permission check:
    # Student 2 CANNOT download Student 1's private doc
    _, _, err_dl = doc_service.check_download_permission(str(doc_priv.id), student2)
    assert err_dl is not None
    assert "không có quyền tải" in err_dl

    # Owner can download
    _, f_path, err_dl = doc_service.check_download_permission(str(doc_priv.id), student1)
    assert err_dl is None
    assert f_path is not None

    # 5. Edit permission check:
    # Student 2 tries to edit Student 1's doc -> rejected
    _, err_edit = doc_service.update_document(
        doc_id=doc_priv.id,
        title="Hacked Title",
        description="",
        subject="Toan",
        is_public=True,
        file_storage=None,
        current_user=student2,
    )
    assert "Bạn không có quyền chỉnh sửa" in err_edit

    # Owner can edit
    updated, err_edit = doc_service.update_document(
        doc_id=doc_priv.id,
        title="Đề ôn tập riêng tư (Đã sửa)",
        description="Đã cập nhật",
        subject="Toán học",
        is_public=False,
        file_storage=None,
        current_user=student1,
    )
    assert err_edit is None
    assert updated.title == "Đề ôn tập riêng tư (Đã sửa)"

    # 6. Comments:
    c, err_c = doc_service.add_comment(doc_priv.id, student1, "Ghi nhớ công thức phần 3")
    assert err_c is None
    assert c is not None

    comments = doc_service.get_comments(doc_priv.id)
    assert len(comments) == 1
    assert comments[0].content == "Ghi nhớ công thức phần 3"

    # 7. Delete permission check:
    # Student 2 CANNOT delete Student 1's doc
    success, err_del = doc_service.delete_document(doc_priv.id, student2)
    assert success is False
    assert "không có quyền xóa" in err_del

    # Admin CAN delete any document
    success, err_del = admin_service.delete_any_document(admin_user, doc_priv.id)
    assert success is True
    assert err_del is None
    assert repos["doc_repo"].get_by_id(doc_priv.id) is None

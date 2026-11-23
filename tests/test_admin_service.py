import pytest
from app.services.auth_service import AuthService
from app.services.admin_service import AdminService
from app.services.document_service import DocumentService
from tests.test_document_service import create_file_storage


def test_admin_service_actions(repos):
    auth_service = AuthService(repos["user_repo"])
    admin_service = AdminService(
        user_repo=repos["user_repo"],
        document_repo=repos["doc_repo"],
        storage_repo=repos["storage_repo"],
    )
    doc_service = DocumentService(
        document_repo=repos["doc_repo"],
        storage_repo=repos["storage_repo"],
        comment_repo=repos["comment_repo"],
    )

    admin_user, _ = auth_service.register("the_admin", "AdminPass123", "admin")
    student, _ = auth_service.register("the_student", "StudentPass123", "student")

    # Non-admin tries admin actions -> rejected
    users, err = admin_service.list_all_users(student)
    assert users is None
    assert "không có quyền" in err

    # Admin lists users -> success
    users, err = admin_service.list_all_users(admin_user)
    assert err is None
    assert len(users) >= 2

    # Admin cannot toggle own status
    success, err = admin_service.toggle_user_status(admin_user, admin_user.id)
    assert success is False
    assert "không thể tự khóa" in err

    # Admin toggles student status -> lock
    success, err = admin_service.toggle_user_status(admin_user, student.id)
    assert success is True
    updated_student = repos["user_repo"].get_by_id(student.id)
    assert updated_student.is_active is False

    # Admin toggles student status again -> unlock
    success, err = admin_service.toggle_user_status(admin_user, student.id)
    assert success is True
    updated_student = repos["user_repo"].get_by_id(student.id)
    assert updated_student.is_active is True

    # Document approve & delete by admin
    pdf = create_file_storage("doc.pdf", b"%PDF content")
    doc, _ = doc_service.create_document(
        title="Pending Doc",
        description="",
        subject="Physics",
        is_public=True,
        file_storage=pdf,
        current_user=student,
    )
    repos["doc_repo"].update_status(doc.id, "pending")

    # Approve
    success, err = admin_service.approve_document(admin_user, doc.id)
    assert success is True
    assert repos["doc_repo"].get_by_id(doc.id).status == "approved"

    # Delete any doc
    success, err = admin_service.delete_any_document(admin_user, doc.id)
    assert success is True
    assert repos["doc_repo"].get_by_id(doc.id) is None

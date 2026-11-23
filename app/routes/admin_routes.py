from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)
from app.services.admin_service import AdminService
from app.repositories.storage_repository import StorageRepository
from app.repositories.document_repository import DocumentRepository
from app.routes.common import admin_required, get_current_user

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def get_admin_service() -> AdminService:
    storage = StorageRepository(
        upload_folder=current_app.config["UPLOAD_FOLDER"],
        allowed_extensions=current_app.config.get("ALLOWED_EXTENSIONS"),
    )
    return AdminService(storage_repo=storage)


@admin_bp.route("/users")
@admin_required
def list_users():
    current_user = get_current_user()
    service = get_admin_service()
    users, err = service.list_all_users(current_user)
    if err:
        flash(err, "danger")
        return redirect(url_for("documents.list_documents"))

    return render_template("admin/users.html", users=users)


@admin_bp.route("/users/<int:user_id>/toggle-status", methods=["POST"])
@admin_required
def toggle_user_status(user_id: int):
    current_user = get_current_user()
    service = get_admin_service()

    success, err = service.toggle_user_status(current_user, user_id)
    if not success:
        flash(err or "Không thể cập nhật trạng thái người dùng.", "danger")
    else:
        flash("Cập nhật trạng thái tài khoản thành công.", "success")

    return redirect(url_for("admin.list_users"))


@admin_bp.route("/documents")
@admin_required
def list_documents():
    doc_repo = DocumentRepository()
    # Admin sees all documents
    docs = doc_repo.search(is_admin=True)
    return render_template("admin/documents.html", documents=docs)


@admin_bp.route("/documents/<int:doc_id>/approve", methods=["POST"])
@admin_required
def approve_document(doc_id: int):
    current_user = get_current_user()
    service = get_admin_service()

    success, err = service.approve_document(current_user, doc_id)
    if not success:
        flash(err or "Không thể duyệt tài liệu.", "danger")
    else:
        flash("Đã duyệt tài liệu thành công.", "success")

    return redirect(url_for("admin.list_documents"))


@admin_bp.route("/documents/<int:doc_id>/delete", methods=["POST"])
@admin_required
def delete_document(doc_id: int):
    current_user = get_current_user()
    service = get_admin_service()

    success, err = service.delete_any_document(current_user, doc_id)
    if not success:
        flash(err or "Không thể xóa tài liệu.", "danger")
    else:
        flash("Đã xóa tài liệu khỏi hệ thống.", "success")

    return redirect(url_for("admin.list_documents"))

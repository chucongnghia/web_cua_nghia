import os
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
    current_app,
)
from app.services.document_service import DocumentService
from app.repositories.storage_repository import StorageRepository
from app.routes.common import get_current_user, login_required

document_bp = Blueprint("documents", __name__)


def get_doc_service() -> DocumentService:
    storage = StorageRepository(
        upload_folder=current_app.config["UPLOAD_FOLDER"],
        allowed_extensions=current_app.config.get("ALLOWED_EXTENSIONS"),
    )
    return DocumentService(storage_repo=storage)


@document_bp.route("/")
def index():
    return redirect(url_for("documents.list_documents"))


@document_bp.route("/documents")
def list_documents():
    keyword = request.args.get("keyword", "")
    subject = request.args.get("subject", "")
    current_user = get_current_user()

    service = get_doc_service()
    docs = service.search_documents(
        keyword=keyword, subject=subject, current_user=current_user
    )
    subjects = service.get_subjects()

    return render_template(
        "documents/list.html",
        documents=docs,
        subjects=subjects,
        selected_subject=subject,
        keyword=keyword,
        is_my_docs=False,
    )


@document_bp.route("/documents/my")
@login_required
def my_documents():
    current_user = get_current_user()
    service = get_doc_service()
    docs = service.list_my_documents(current_user)
    subjects = service.get_subjects()

    return render_template(
        "documents/list.html",
        documents=docs,
        subjects=subjects,
        selected_subject="",
        keyword="",
        is_my_docs=True,
    )


@document_bp.route("/documents/new", methods=["GET", "POST"])
@login_required
def create_document():
    current_user = get_current_user()
    service = get_doc_service()

    if request.method == "POST":
        title = request.form.get("title", "")
        description = request.form.get("description", "")
        subject = request.form.get("subject", "")
        is_public = request.form.get("is_public") == "1"
        file = request.files.get("file")

        doc, err = service.create_document(
            title=title,
            description=description,
            subject=subject,
            is_public=is_public,
            file_storage=file,
            current_user=current_user,
        )

        if err:
            flash(err, "danger")
            return render_template(
                "documents/form.html",
                title=title,
                description=description,
                subject=subject,
                is_public=is_public,
                action="create",
            )

        flash("Tải lên tài liệu thành công!", "success")
        return redirect(url_for("documents.view_document", doc_id=doc.id))

    return render_template(
        "documents/form.html",
        title="",
        description="",
        subject="",
        is_public=True,
        action="create",
    )


@document_bp.route("/documents/<int:doc_id>")
def view_document(doc_id: int):
    current_user = get_current_user()
    service = get_doc_service()

    doc, err = service.get_document_for_view(doc_id, current_user)
    if err:
        flash(err, "warning")
        return redirect(url_for("documents.list_documents"))

    comments = service.get_comments(doc_id)
    return render_template(
        "documents/detail.html",
        document=doc,
        comments=comments,
    )


@document_bp.route("/documents/<int:doc_id>/edit", methods=["GET", "POST"])
@login_required
def edit_document(doc_id: int):
    current_user = get_current_user()
    service = get_doc_service()

    doc, err = service.get_document_for_view(doc_id, current_user)
    if err or not doc:
        flash(err or "Không tìm thấy tài liệu.", "warning")
        return redirect(url_for("documents.list_documents"))

    # Only owner or admin can edit
    if not current_user.is_admin() and doc.owner_id != current_user.id:
        flash("Bạn không có quyền chỉnh sửa tài liệu này.", "danger")
        return redirect(url_for("documents.view_document", doc_id=doc.id))

    if request.method == "POST":
        title = request.form.get("title", "")
        description = request.form.get("description", "")
        subject = request.form.get("subject", "")
        is_public = request.form.get("is_public") == "1"
        file = request.files.get("file")

        updated_doc, update_err = service.update_document(
            doc_id=doc.id,
            title=title,
            description=description,
            subject=subject,
            is_public=is_public,
            file_storage=file,
            current_user=current_user,
        )

        if update_err:
            flash(update_err, "danger")
            return render_template(
                "documents/form.html",
                document=doc,
                title=title,
                description=description,
                subject=subject,
                is_public=is_public,
                action="edit",
            )

        flash("Cập nhật tài liệu thành công!", "success")
        return redirect(url_for("documents.view_document", doc_id=doc.id))

    return render_template(
        "documents/form.html",
        document=doc,
        title=doc.title,
        description=doc.description,
        subject=doc.subject,
        is_public=doc.is_public,
        action="edit",
    )


@document_bp.route("/documents/<int:doc_id>/delete", methods=["POST"])
@login_required
def delete_document(doc_id: int):
    current_user = get_current_user()
    service = get_doc_service()

    success, err = service.delete_document(doc_id, current_user)
    if not success:
        flash(err or "Không thể xóa tài liệu.", "danger")
        return redirect(url_for("documents.view_document", doc_id=doc_id))

    flash("Đã xóa tài liệu thành công.", "success")
    return redirect(url_for("documents.list_documents"))


@document_bp.route("/documents/<int:doc_id>/download")
def download_document(doc_id: int):
    current_user = get_current_user()
    service = get_doc_service()

    doc, file_path, err = service.check_download_permission(
        str(doc_id), current_user
    )
    if err:
        flash(err, "warning")
        return redirect(url_for("documents.list_documents"))

    return send_file(
        file_path,
        as_attachment=True,
        download_name=doc.original_filename,
    )


@document_bp.route("/download/<path:filename>")
def download_by_filename(filename: str):
    """
    Direct download by filename endpoint (verifies permissions safely).
    """
    current_user = get_current_user()
    service = get_doc_service()

    doc, file_path, err = service.check_download_permission(
        filename, current_user
    )
    if err:
        flash(err, "warning")
        return redirect(url_for("documents.list_documents"))

    return send_file(
        file_path,
        as_attachment=True,
        download_name=doc.original_filename,
    )


@document_bp.route("/documents/<int:doc_id>/comments", methods=["POST"])
@login_required
def add_comment(doc_id: int):
    current_user = get_current_user()
    content = request.form.get("content", "")

    service = get_doc_service()
    comment, err = service.add_comment(doc_id, current_user, content)
    if err:
        flash(err, "danger")
    else:
        flash("Đã thêm bình luận thành công.", "success")

    return redirect(url_for("documents.view_document", doc_id=doc_id))

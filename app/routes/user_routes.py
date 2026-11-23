from flask import Blueprint, render_template, jsonify
from app.repositories.document_repository import DocumentRepository
from app.routes.common import get_current_user, login_required

user_bp = Blueprint("user", __name__)


@user_bp.route("/profile")
@login_required
def profile():
    user = get_current_user()
    doc_repo = DocumentRepository()
    uploaded_count = doc_repo.count_by_owner(user.id)
    return render_template(
        "user/profile.html",
        user=user,
        uploaded_count=uploaded_count,
    )


@user_bp.route("/api/user/me")
def api_me():
    user = get_current_user()
    if not user:
        return jsonify({"authenticated": False, "error": "Chưa đăng nhập"}), 401
    return jsonify({
        "authenticated": True,
        "user": user.to_dict(),
    })

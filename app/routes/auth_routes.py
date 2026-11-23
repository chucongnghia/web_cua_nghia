from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.auth_service import AuthService
from app.services.logger_service import log_activity
from app.routes.common import get_current_user

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if get_current_user():
        return redirect(url_for("documents.list_documents"))

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        role = request.form.get("role", "student")

        if password != confirm_password:
            flash("Mật khẩu xác nhận không khớp.", "danger")
            return render_template("auth/register.html", username=username, role=role)

        auth_service = AuthService()
        user, err = auth_service.register(username, password, role)
        if err:
            flash(err, "danger")
            return render_template("auth/register.html", username=username, role=role)

        flash("Đăng ký thành công! Vui lòng đăng nhập.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if get_current_user():
        return redirect(url_for("documents.list_documents"))

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        auth_service = AuthService()
        user, err = auth_service.authenticate(username, password)
        if err:
            flash(err, "danger")
            return render_template("auth/login.html", username=username)

        session.clear()
        session["user_id"] = user.id
        session["username"] = user.username
        session["role"] = user.role

        flash(f"Xin chào {user.username}, bạn đã đăng nhập thành công!", "success")
        next_url = request.args.get("next")
        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        return redirect(url_for("documents.list_documents"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    user = get_current_user()
    if user:
        log_activity(
            action="USER_LOGOUT",
            username=user.username,
            details=f"User ID={user.id} logged out",
        )
    session.clear()
    flash("Bạn đã đăng xuất khỏi hệ thống.", "info")
    return redirect(url_for("auth.login"))

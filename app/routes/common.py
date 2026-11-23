from functools import wraps
from flask import g, session, redirect, url_for, flash, request
from typing import Optional
from app.models.user import User
from app.repositories.user_repository import UserRepository


def get_current_user() -> Optional[User]:
    if "current_user" in g:
        return g.current_user

    user_id = session.get("user_id")
    if not user_id:
        g.current_user = None
        return None

    repo = UserRepository()
    user = repo.get_by_id(user_id)
    # If account was locked after session started
    if user and not user.is_active:
        session.clear()
        g.current_user = None
        return None

    g.current_user = user
    return user


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            flash("Vui lòng đăng nhập để tiếp tục.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            flash("Vui lòng đăng nhập với tư cách quản trị viên.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        if not user.is_admin():
            flash("Bạn không có quyền truy cập vào trang này.", "danger")
            return redirect(url_for("documents.list_documents"))
        return f(*args, **kwargs)

    return decorated_function

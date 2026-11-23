from typing import Optional, Tuple
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.logger_service import log_activity


class AuthService:
    def __init__(self, user_repo: Optional[UserRepository] = None):
        self.user_repo = user_repo or UserRepository()

    def register(
        self, username: str, password: str, role: str = "student"
    ) -> Tuple[Optional[User], Optional[str]]:
        username = (username or "").strip()
        password = password or ""
        role = (role or "student").strip().lower()

        if not username:
            return None, "Tên đăng nhập không được để trống."
        if len(username) < 3 or len(username) > 30:
            return None, "Tên đăng nhập phải có từ 3 đến 30 ký tự."
        if not username.replace("_", "").isalnum():
            return None, "Tên đăng nhập chỉ được chứa chữ cái, số và dấu gạch dưới."

        if not password:
            return None, "Mật khẩu không được để trống."
        if len(password) < 6:
            return None, "Mật khẩu phải có ít nhất 6 ký tự."

        if role not in ("student", "admin"):
            role = "student"

        existing = self.user_repo.get_by_username(username)
        if existing:
            return None, "Tên đăng nhập đã tồn tại trong hệ thống."

        password_hash = generate_password_hash(password)
        new_user = self.user_repo.create(
            username=username,
            password_hash=password_hash,
            role=role,
            is_active=True,
        )

        log_activity(
            action="USER_REGISTER",
            username=username,
            details=f"User registered with role '{role}' (ID={new_user.id})",
        )
        return new_user, None

    def authenticate(
        self, username: str, password: str
    ) -> Tuple[Optional[User], Optional[str]]:
        username = (username or "").strip()
        password = password or ""

        if not username or not password:
            return None, "Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu."

        user = self.user_repo.get_by_username(username)
        if not user:
            log_activity(
                action="LOGIN_FAILED",
                username=username,
                details="Tên đăng nhập không tồn tại",
                level="WARNING",
            )
            return None, "Tên đăng nhập hoặc mật khẩu không chính xác."

        if not user.is_active:
            log_activity(
                action="LOGIN_BLOCKED",
                username=username,
                details=f"Đăng nhập bị từ chối do tài khoản ID={user.id} đã bị khóa",
                level="WARNING",
            )
            return None, "Tài khoản của bạn đã bị khóa. Vui lòng liên hệ quản trị viên."

        if not check_password_hash(user.password_hash, password):
            log_activity(
                action="LOGIN_FAILED",
                username=username,
                details="Sai mật khẩu",
                level="WARNING",
            )
            return None, "Tên đăng nhập hoặc mật khẩu không chính xác."

        log_activity(
            action="LOGIN_SUCCESS",
            username=username,
            details=f"Đăng nhập thành công với vai trò '{user.role}'",
        )
        return user, None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.user_repo.get_by_id(user_id)

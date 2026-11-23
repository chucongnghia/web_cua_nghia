import pytest
from app.services.auth_service import AuthService


def test_register_success(repos):
    service = AuthService(repos["user_repo"])
    user, err = service.register("student_test", "Password123", "student")

    assert err is None
    assert user is not None
    assert user.username == "student_test"
    assert user.role == "student"
    assert user.is_active is True


def test_register_validation_errors(repos):
    service = AuthService(repos["user_repo"])

    # Empty username
    _, err = service.register("", "Password123")
    assert "Tên đăng nhập không được để trống" in err

    # Short username
    _, err = service.register("ab", "Password123")
    assert "từ 3 đến 30 ký tự" in err

    # Invalid characters in username
    _, err = service.register("user@test!", "Password123")
    assert "chỉ được chứa chữ cái, số" in err

    # Short password
    _, err = service.register("valid_user", "12345")
    assert "ít nhất 6 ký tự" in err

    # Duplicate username
    service.register("duplicate_user", "Password123")
    _, err = service.register("duplicate_user", "Password456")
    assert "đã tồn tại" in err


def test_authenticate(repos):
    service = AuthService(repos["user_repo"])
    service.register("login_user", "SecretPass123")

    # Correct credentials
    user, err = service.authenticate("login_user", "SecretPass123")
    assert err is None
    assert user is not None
    assert user.username == "login_user"

    # Wrong password
    _, err = service.authenticate("login_user", "WrongPassword")
    assert err is not None
    assert "không chính xác" in err

    # Non-existent user
    _, err = service.authenticate("nobody", "SecretPass123")
    assert err is not None
    assert "không chính xác" in err

    # Locked user
    repos["user_repo"].update_status(user.id, False)
    _, err = service.authenticate("login_user", "SecretPass123")
    assert err is not None
    assert "đã bị khóa" in err

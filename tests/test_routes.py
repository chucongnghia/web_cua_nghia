import io
import pytest


def test_routes_end_to_end(client):
    # 1. Register student account via form
    res = client.post(
        "/auth/register",
        data={
            "username": "tester_sv",
            "password": "Password123",
            "confirm_password": "Password123",
            "role": "student",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200

    # Register admin account
    res = client.post(
        "/auth/register",
        data={
            "username": "tester_ad",
            "password": "AdminPassword123",
            "confirm_password": "AdminPassword123",
            "role": "admin",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200

    # 2. Login as student
    res = client.post(
        "/auth/login",
        data={"username": "tester_sv", "password": "Password123"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert "tester_sv" in res.text

    # 3. Check /api/user/me JSON API
    res = client.get("/api/user/me")
    assert res.status_code == 200
    data = res.get_json()
    assert data["authenticated"] is True
    assert data["user"]["username"] == "tester_sv"

    # 4. View profile & my documents
    res = client.get("/profile")
    assert res.status_code == 200
    assert "Hồ sơ tài khoản" in res.text

    res = client.get("/documents/my")
    assert res.status_code == 200
    assert "Tài liệu do tôi tải lên" in res.text

    # 5. Upload a document
    file_content = b"%PDF-1.4 test document stream"
    res = client.post(
        "/documents/new",
        data={
            "title": "Tài liệu kiểm thử tích hợp",
            "subject": "Kiểm thử phần mềm",
            "description": "Mô tả tài liệu kiểm thử",
            "is_public": "1",
            "file": (io.BytesIO(file_content), "test_lecture.pdf"),
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert "Tài liệu kiểm thử tích hợp" in res.text

    # 6. Add a comment
    res = client.post(
        "/documents/1/comments",
        data={"content": "Bình luận thử nghiệm đầu tiên"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert "Bình luận thử nghiệm đầu tiên" in res.text

    # 7. Download file via doc id
    res = client.get("/documents/1/download")
    assert res.status_code == 200
    assert res.data == file_content

    # 8. Student tries to access admin page -> redirected
    res = client.get("/admin/users", follow_redirects=True)
    assert res.status_code == 200
    assert "Bạn không có quyền truy cập" in res.text

    # 9. Logout student and login as admin
    client.get("/auth/logout", follow_redirects=True)

    res = client.post(
        "/auth/login",
        data={"username": "tester_ad", "password": "AdminPassword123"},
        follow_redirects=True,
    )
    assert res.status_code == 200

    # 10. Admin views users list
    res = client.get("/admin/users")
    assert res.status_code == 200
    assert "tester_sv" in res.text

    # 11. Admin views documents list
    res = client.get("/admin/documents")
    assert res.status_code == 200
    assert "Tài liệu kiểm thử tích hợp" in res.text

    # 12. Admin toggles student lock
    res = client.post("/admin/users/1/toggle-status", follow_redirects=True)
    assert res.status_code == 200
    assert "Cập nhật trạng thái tài khoản thành công" in res.text

    # 13. Student now cannot login
    client.get("/auth/logout", follow_redirects=True)
    res = client.post(
        "/auth/login",
        data={"username": "tester_sv", "password": "Password123"},
        follow_redirects=True,
    )
    assert "Tài khoản của bạn đã bị khóa" in res.text

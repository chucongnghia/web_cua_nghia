# StudyDocs (v0) - Hệ thống Quản lý Tài liệu Học tập

Hệ thống Quản lý Tài liệu Học tập (**StudyDocs**) phiên bản đầu tiên (**v0**) được phát triển bằng **Python 3.11+**, **Flask**, **Jinja2** và **SQLite**. Dự án được thiết kế chuyên biệt phục vụ bài tập lớn môn **Lập trình An toàn và Kiểm thử (LTATKT)**.

---

## 1. Kiến trúc & Tổ chức mã nguồn (3-Tier Architecture)

Mã nguồn được phân tách triệt để thành 3 lớp độc lập giúp việc kiểm thử tự động (Unit Test / Integration Test) bằng `pytest` đạt độ bao phủ cao và tách biệt hoàn toàn phụ thuộc:

```
tiny_project/
├── app/
│   ├── __init__.py              # Application Factory (create_app), cấu hình Flask & Context Processors
│   ├── config.py                # Cấu hình môi trường (DevelopmentConfig, TestingConfig)
│   ├── models/                  # Lớp đối tượng thực thể (Domain Models)
│   │   ├── user.py              # User model & dataclass
│   │   ├── document.py          # Document model & dataclass
│   │   └── comment.py           # Comment model & dataclass
│   ├── repositories/           # Lớp 3: Truy cập dữ liệu (Data Access Layer)
│   │   ├── db.py                # Quản lý kết nối SQLite, khởi tạo Schema, hỗ trợ tìm kiếm Tiếng Việt
│   │   ├── user_repository.py   # Thao tác CSDL bảng 'users'
│   │   ├── document_repository.py # Thao tác CSDL bảng 'documents' (Search, Filter, CRUD)
│   │   ├── comment_repository.py  # Thao tác CSDL bảng 'comments'
│   │   └── storage_repository.py  # Thao tác lưu/đọc/xóa tệp trên ổ đĩa, phòng chống Path Traversal
│   ├── services/               # Lớp 2: Xử lý nghiệp vụ (Business Logic Layer)
│   │   ├── auth_service.py      # Đăng ký, băm mật khẩu, đăng nhập, kiểm tra khóa tài khoản
│   │   ├── document_service.py  # Nghiệp vụ tài liệu, kiểm tra quyền sở hữu/công khai, tải tệp, bình luận
│   │   ├── admin_service.py     # Nghiệp vụ quản trị: khóa/mở khóa user, duyệt & xóa tài liệu
│   │   └── logger_service.py    # Ghi nhật ký có cấu trúc ra file app.log
│   ├── routes/                 # Lớp 1: Tiếp nhận dữ liệu & Điều hướng (Presentation / Controllers)
│   │   ├── common.py            # Middleware: login_required, admin_required, get_current_user
│   │   ├── auth_routes.py       # Tuyến: /auth/login, /auth/register, /auth/logout
│   │   ├── document_routes.py   # Tuyến: /, /documents, /documents/new, /documents/<id>, /download
│   │   ├── admin_routes.py      # Tuyến: /admin/users, /admin/documents, /admin/...
│   │   └── user_routes.py       # Tuyến: /profile, /api/user/me
│   ├── static/
│   │   └── css/style.css        # Giao diện CSS hiện đại, trực quan, hỗ trợ responsive
│   └── templates/               # Giao diện Jinja2 (HTML5)
│       ├── base.html            # Khung giao diện chuẩn, navbar, flash messages, footer
│       ├── auth/                # Giao diện đăng nhập, đăng ký
│       ├── documents/           # Danh sách, chi tiết, thêm/sửa tài liệu
│       ├── admin/               # Quản trị người dùng & duyệt tài liệu
│       └── user/                # Trang thông tin tài khoản cá nhân
├── uploads/                     # Thư mục lưu trữ tệp đính kèm an toàn (PDF, DOCX, TXT)
├── tests/                       # Bộ kiểm thử tự động với pytest
│   ├── conftest.py              # Cấu hình CSDL in-memory (:memory:) & fixture test
│   ├── test_repositories.py     # Unit test cho tầng Repositories & File Storage
│   ├── test_auth_service.py     # Unit test cho AuthService
│   ├── test_document_service.py # Unit test cho DocumentService & Phân quyền tài nguyên
│   ├── test_admin_service.py    # Unit test cho AdminService & Thao tác đặc quyền
│   └── test_routes.py           # Integration test luồng End-to-End
├── seed.py                      # Kịch bản nạp dữ liệu mẫu (Admin, 2 Sinh viên, Tài liệu, Bình luận)
├── run.py                       # Điểm khởi chạy ứng dụng web StudyDocs
├── requirements.txt             # Danh sách thư viện phụ thuộc
├── app.log                      # Tệp nhật ký ghi nhận các hành vi nhạy cảm
├── PROMPT_LOG.md                # Nhật ký sinh mã và phân tích an toàn Buổi 1
└── README.md                    # Tài liệu hướng dẫn sử dụng và kiểm thử
```

---

## 2. Đặc tả 5 Nội dung Bảo vệ Dữ liệu theo Đề tài BTL

| STT | Yêu cầu | Hiện thực trong StudyDocs (v0) |
|---|---|---|
| **1** | **Xác thực người dùng** | Sử dụng phiên làm việc (Session-based Auth). Mật khẩu được băm một chiều an toàn bằng thuật toán chuẩn `werkzeug.security` (PBKDF2/scrypt). Kiểm tra trạng thái tài khoản `is_active` trước khi cho phép phiên hoạt động. |
| **2** | **Điểm tiếp nhận & Điều kiện hợp lệ** | Điểm tiếp nhận: Biểu mẫu form đăng ký/đăng nhập, tạo tài liệu, tải tệp (`request.form`, `request.files`).<br>Điều kiện hợp lệ: Username (3-30 ký tự, `[a-zA-Z0-9_]`), Mật khẩu ($\ge 6$ ký tự), Tiêu đề ($\le 200$ ký tự), Môn học ($\le 100$ ký tự), Định dạng tệp chỉ chấp nhận whitelist: `.pdf`, `.docx`, `.txt` với dung lượng $\le 16\text{ MB}$. |
| **3** | **Nơi đọc/ghi CSDL và Tệp** | - CSDL: Tập trung tại tầng Repositories (`UserRepository`, `DocumentRepository`, `CommentRepository`) sử dụng SQLite Parameterized Queries (`?`) phòng chống SQL Injection (V1).<br>- Tệp: `StorageRepository` lưu vào thư mục `uploads/` với tên tệp ngẫu nhiên `uuid_prefix + secure_filename`, kiểm tra biên đường dẫn chống Path Traversal (V12). |
| **4** | **Nơi xuất dữ liệu & Nhật ký** | - HTML templates được Jinja2 tự động mã hóa ký tự (Auto-escaping) chống XSS (V3).<br>- API JSON `/api/user/me` chỉ xuất thông tin cơ bản của tài khoản hiện hành (không để lộ `password_hash`).<br>- File `app.log` ghi lại có cấu trúc: thời gian, tên user, sự kiện (LOGIN, UPLOAD, UPDATE, DELETE, DOWNLOAD, ADMIN_TOGGLE_USER_STATUS). |
| **5** | **Vai trò & Ma trận phân quyền** | - **Sinh viên (`student`)**: Đăng ký/đăng nhập, tải lên tài liệu, xem tài liệu công khai (`is_public=1`) và tài liệu riêng tư của chính mình (`is_public=0 AND owner_id=user.id`), sửa/xóa tài liệu do mình tải lên, tải tệp đính kèm hợp lệ, gửi bình luận.<br>- **Quản trị viên (`admin`)**: Toàn bộ quyền của sinh viên, xem trang quản trị người dùng, khóa/mở khóa tài khoản sinh viên, xem toàn bộ tài liệu (công khai & riêng tư), duyệt tài liệu và xóa bất kỳ tài liệu nào trong hệ thống. |

---

## 3. Ma trận Phân quyền Tài nguyên

| Thao tác / Tài nguyên | Khách vãng lai (Chưa đăng nhập) | Sinh viên (Chủ sở hữu) | Sinh viên khác | Quản trị viên (Admin) |
|---|:---:|:---:|:---:|:---:|
| Xem danh sách & tìm kiếm tài liệu công khai | ✅ | ✅ | ✅ | ✅ |
| Xem tài liệu riêng tư (`private`) | ❌ | ✅ | ❌ | ✅ |
| Tải tệp đính kèm công khai | ✅ | ✅ | ✅ | ✅ |
| Tải tệp đính kèm riêng tư | ❌ | ✅ | ❌ (Chặn quyền) | ✅ |
| Tạo / Tải lên tài liệu mới | ❌ (Yêu cầu login) | ✅ | ✅ | ✅ |
| Sửa / Xóa tài liệu | ❌ | ✅ | ❌ (Từ chối 403) | ✅ |
| Gửi bình luận / Ghi chú | ❌ (Yêu cầu login) | ✅ | ✅ | ✅ |
| Quản trị người dùng (Khóa/Mở khóa) | ❌ | ❌ (Chặn 403) | ❌ (Chặn 403) | ✅ (Không tự khóa mình) |
| Duyệt / Xóa tài liệu bất kỳ | ❌ | ❌ | ❌ | ✅ |

---

## 4. Hướng dẫn Cài đặt & Chạy ứng dụng

### Yêu cầu hệ thống:
- Python 3.11 trở lên (khuyến nghị Python 3.11, 3.12 hoặc 3.13+)
- Trình quản lý gói `pip`

### Bước 1: Cài đặt thư viện phụ thuộc
Mở terminal/PowerShell tại thư mục dự án và thực hiện:
```bash
pip install -r requirements.txt
```

### Bước 2: Khởi tạo dữ liệu mẫu (Seed Data)
Chạy kịch bản khởi tạo database `studydocs.db` và các tệp đính kèm mẫu:
```bash
python seed.py
```
> **Dữ liệu tài khoản mẫu được tạo sẵn:**
> - **Quản trị viên (Admin):** Username: `admin` | Password: `Admin@123`
> - **Sinh viên A:** Username: `student_a` | Password: `StudentA@123`
> - **Sinh viên B:** Username: `student_b` | Password: `StudentB@123`

### Bước 3: Khởi chạy máy chủ Web
Khởi động ứng dụng Flask:
```bash
python run.py
```
Truy cập ứng dụng tại trình duyệt web: **http://127.0.0.1:5000**

---

## 5. Hướng dẫn Chạy Kiểm thử (Unit & Integration Tests)

Dự án đi kèm bộ test tự động toàn diện được cấu hình chạy trên CSDL SQLite bộ nhớ (`:memory:`) độc lập:

1. **Chạy toàn bộ kiểm thử:**
   ```bash
   python -m pytest -v
   ```

2. **Chạy kiểm thử và kiểm tra tỷ lệ bao phủ mã nguồn (Coverage):**
   ```bash
   python -m pytest --cov=app --cov-report=term-missing
   ```

*(Kết quả nghiệm thu: Toàn bộ 10/10 test case vượt qua thành công, tỷ lệ bao phủ mã nguồn đạt trên **83%**).*

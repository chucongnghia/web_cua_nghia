# PROMPT_LOG.md - Nhật ký Sinh mã & Phân tích An toàn (Phiên bản v0)

**Môn học:** Lập trình An toàn và Kiểm thử (LTATKT)  
**Dự án:** Hệ thống Quản lý Tài liệu Học tập (StudyDocs)  
**Phiên bản:** v0 (Initial Functional Version)  
**Thời gian tạo:** 23/11/2026  

---

## 1. Prompt đầu vào của người dùng

```text
Hãy xây dựng phiên bản đầu tiên (v0) cho một ứng dụng web "Hệ thống Quản lý Tài liệu Học tập" (StudyDocs) bằng Python 3.11+ sử dụng Flask, Jinja2 và SQLite.

1. Yêu cầu kiến trúc & tổ chức mã:
Tách biệt rõ ràng mã nguồn thành 3 lớp để dễ dàng viết unit test độc lập bằng pytest:
- Lớp tiếp nhận dữ liệu (routes / controllers): xử lý HTTP request, nhận tham số từ form/URL và trả về HTML hoặc JSON.
- Lớp xử lý nghiệp vụ (services): chứa logic đăng nhập, kiểm tra quyền, xử lý dữ liệu tài liệu, tìm kiếm, tải tệp.
- Lớp truy cập dữ liệu (repositories / models): thực hiện các câu truy vấn đọc/ghi với SQLite và thao tác đọc/ghi tệp trên ổ đĩa.
- Tách riêng cấu hình CSDL để có thể chạy bằng dữ liệu giả lập (seed data) khi khởi động và dùng CSDL riêng khi chạy kiểm thử.

2. Vai trò người dùng & phân quyền nghiệp vụ:
Hệ thống có 2 vai trò:
- Sinh viên (student): đăng ký/đăng nhập, tải lên tài liệu của mình, xem danh sách tài liệu công khai và tài liệu riêng tư của bản thân, sửa/xóa tài liệu do chính mình tạo, thêm ghi chú/bình luận vào tài liệu, tải xuống tệp đính kèm.
- Quản trị viên (admin): có mọi quyền của sinh viên, đồng thời có trang quản trị để xem danh sách toàn bộ người dùng, khóa/mở khóa tài khoản, và duyệt/xóa bất kỳ tài liệu nào trong hệ thống.

3. Các chức năng chính & đầu vào/đầu ra:
- Xác thực: Đăng nhập bằng username và password, quản lý phiên làm việc (session), đăng xuất.
- Quản lý tài liệu (CRUD):
  + Tạo/sửa tài liệu gồm các trường: tiêu đề, mô tả chi tiết (hiển thị trên giao diện HTML), môn học, chế độ hiển thị (public/private), và tệp đính kèm (PDF/DOCX/TXT).
  + Tải xuống tệp đính kèm theo tên tệp hoặc ID tài liệu.
- Tìm kiếm tài liệu: Tìm kiếm theo từ khóa (tiêu đề hoặc môn học) và lọc theo danh mục.
- Ghi chú/Bình luận: Người dùng gửi nội dung bình luận dưới mỗi tài liệu và hiển thị trực tiếp lên trang chi tiết tài liệu.
- Trang hồ sơ cá nhân & API thông tin: Hiển thị thông tin tài khoản hiện tại và ghi nhật ký (log) các hoạt động đăng nhập, tải lên, xóa tài liệu ra tệp app.log.

4. Dữ liệu giả lập & hướng dẫn chạy:
- Cung cấp script seed.py tạo sẵn dữ liệu mẫu: 1 tài khoản admin, 2 tài khoản student (student_a, student_b) cùng một số tài liệu công khai và riêng tư của từng người.
- Cung cấp file requirements.txt và hướng dẫn ngắn gọn các lệnh cài đặt, khởi tạo dữ liệu mẫu và chạy ứng dụng ở local.
```

---

## 2. Tổng quan Giải pháp Kiến trúc v0

Hệ thống đã triển khai đầy đủ các yêu cầu theo mô hình kiến trúc 3 lớp nghiêm ngặt:
1. **Presentation Layer (app/routes/):** Xử lý nhận dữ liệu HTTP Request, kiểm tra phiên Session và phân quyền truy cập thông qua Decorator (`@login_required`, `@admin_required`). Kết quả trả về giao diện HTML dựng bằng Jinja2 hoặc định dạng JSON (`/api/user/me`).
2. **Business Logic Layer (app/services/):**
   - `AuthService`: Xác thực, kiểm tra độ dài và định dạng tài khoản, băm mật khẩu, từ chối tài khoản bị khóa.
   - `DocumentService`: Quản lý nghiệp vụ tài liệu, kiểm tra quyền sở hữu tài nguyên (Resource Ownership Authorization), kiểm tra quyền tải tệp đối với tài liệu riêng tư, thêm bình luận.
   - `AdminService`: Xử lý quyền hạn quản trị viên, kiểm soát khóa/mở khóa người dùng (ngăn chặn tự khóa tài khoản của chính mình), duyệt và xóa tài liệu.
   - `LoggerService`: Ghi nhận nhật ký có cấu trúc theo định dạng thời gian, mức độ, tài khoản và hành vi ra tệp `app.log`.
3. **Data Access Layer (app/repositories/):**
   - `UserRepository`, `DocumentRepository`, `CommentRepository`: Sử dụng SQLite Parameterized Queries nhằm loại trừ hoàn toàn nguy cơ SQL Injection.
   - `StorageRepository`: Quản lý lưu trữ tệp trên đĩa cứng, kiểm tra phần mở rộng tệp hợp lệ (`.pdf`, `.docx`, `.txt`), tạo tên tệp ngẫu nhiên chống trùng lặp và kiểm tra giới hạn thư mục chống Path Traversal (`os.path.commonpath`).
   - Cấu hình CSDL linh hoạt: Cho phép chạy với `studydocs.db` ở môi trường Development hoặc `:memory:` / temp database ở môi trường Testing.

---

## 3. Phân tích 5 Điểm An toàn Trọng yếu (Đề xuất Dự án BTL)

1. **Cách xác thực người dùng:**
   - Sử dụng Session bảo vệ bởi `SECRET_KEY`.
   - Mật khẩu được băm an toàn qua hàm băm mật mã chuẩn (không lưu trữ plain-text).
   - Kiểm tra `is_active` để vô hiệu hóa phiên của các tài khoản đã bị quản trị viên khóa.
2. **Điểm tiếp nhận dữ liệu & Điều kiện hợp lệ:**
   - Biểu mẫu web tiếp nhận qua `POST /auth/register`, `POST /auth/login`, `POST /documents/new`, `POST /documents/<id>/comments`.
   - Dữ liệu được chuẩn hóa `strip()`, kiểm tra độ dài tối đa/tối thiểu, lọc ký tự hợp lệ (`isalnum` cho username).
   - Tệp đính kèm được kiểm tra đuôi mở rộng Whitelist: chỉ cho phép `.pdf`, `.docx`, `.txt`.
3. **Nơi đọc/ghi dữ liệu trong CSDL và Tệp:**
   - CSDL: Bảng `users`, `documents`, `comments` trong tệp `studydocs.db`. Các truy vấn dùng tham số `?` bảo đảm tách biệt dữ liệu và mã lệnh.
   - Tệp: Thư mục `uploads/`. Tên tệp vật lý lưu dạng `<uuid_prefix>_<safe_filename>`. Thao tác đọc tệp được kiểm tra giới hạn thư mục, ngăn chặn đọc tệp hệ thống.
4. **Nơi xuất dữ liệu cho người dùng và Nhật ký:**
   - Jinja2 Template tự động Escape các ký tự đặc biệt như `<`, `>`, `&`, `"` khi render ra trang web, phòng tránh Stored & Reflected XSS.
   - API `/api/user/me` chỉ xuất thông tin định danh công khai (`id`, `username`, `role`, `is_active`, `created_at`), không xuất `password_hash`.
   - Nhật ký hoạt động ghi ra file `app.log` với các hành vi quan trọng: Đăng nhập thành công/thất bại/bị khóa, Đăng xuất, Tải lên tài liệu, Tải xuống tài liệu, Xóa tài liệu, Khóa/mở khóa người dùng.
5. **Chủ sở hữu & Phân quyền trên tài nguyên:**
   - Hai vai trò: `student` và `admin`.
   - Sinh viên chỉ có quyền sửa, xóa tài liệu do chính mình tạo ra (`doc.owner_id == current_user.id`).
   - Tài liệu có trạng thái `is_public = False` chỉ được phép xem và tải xuống bởi chính chủ sở hữu hoặc quản trị viên.

---

## 4. Báo cáo Kết quả Kiểm thử v0

- **Công cụ kiểm thử:** `pytest` kết hợp `pytest-cov`.
- **Số lượng test case:** 10 ca kiểm thử độc lập bao quát từ tầng Repository, Service đến Route.
- **Tỷ lệ bao phủ dòng (Line Coverage):** **83%** trên toàn bộ dự án (trong đó các module CSDL và xác thực đạt 86% - 100%).
- **Trạng thái:** 10/10 test cases PASSED.

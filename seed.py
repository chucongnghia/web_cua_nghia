import os
from werkzeug.security import generate_password_hash
from app.config import BaseConfig
from app.repositories.db import init_db, connect_db
from app.repositories.user_repository import UserRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.comment_repository import CommentRepository
from app.repositories.storage_repository import StorageRepository


def run_seed():
    db_path = BaseConfig.DATABASE_PATH
    upload_folder = BaseConfig.UPLOAD_FOLDER

    print(f"[*] Khởi tạo cơ sở dữ liệu tại: {db_path}")
    init_db(db_path)

    conn = connect_db(db_path)
    user_repo = UserRepository(conn)
    doc_repo = DocumentRepository(conn)
    comment_repo = CommentRepository(conn)
    storage_repo = StorageRepository(upload_folder)

    # Clean existing data for clean seed
    conn.execute("DELETE FROM comments")
    conn.execute("DELETE FROM documents")
    conn.execute("DELETE FROM users")
    conn.commit()

    print("[*] Tạo người dùng mẫu...")
    admin = user_repo.create(
        username="admin",
        password_hash=generate_password_hash("Admin@123"),
        role="admin",
        is_active=True,
    )

    student_a = user_repo.create(
        username="student_a",
        password_hash=generate_password_hash("StudentA@123"),
        role="student",
        is_active=True,
    )

    student_b = user_repo.create(
        username="student_b",
        password_hash=generate_password_hash("StudentB@123"),
        role="student",
        is_active=True,
    )

    print(f" -> Đã tạo 3 tài khoản: admin (ID={admin.id}), student_a (ID={student_a.id}), student_b (ID={student_b.id})")

    print("[*] Tạo tệp và tài liệu học tập mẫu...")
    # 1. Public doc for student_a
    fn1, orig1, size1 = storage_repo.save_raw_content(
        "Giao_trinh_DSA.pdf",
        b"%PDF-1.4\n% Sample PDF for StudyDocs DSA Course\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF",
    )
    doc1 = doc_repo.create(
        title="Giáo trình Cấu trúc dữ liệu và Giải thuật",
        description="Tài liệu tham khảo toàn diện về Danh sách liên kết, Cây nhị phân tìm kiếm, Đồ thị và các giải thuật sắp xếp kinh điển.",
        subject="Cấu trúc dữ liệu",
        is_public=True,
        filename=fn1,
        original_filename=orig1,
        file_size=size1,
        owner_id=student_a.id,
        status="approved",
    )

    # 2. Private doc for student_a
    fn2, orig2, size2 = storage_repo.save_raw_content(
        "Ghi_chu_on_thi_Giai_tich.txt",
        "Ghi chu ca nhan on thi Giai tich 1:\n- Chuong 1: Gioi han va lien tuc\n- Chuong 2: Dao ham va vi phan\n- Chuong 3: Tich phan suy rong".encode("utf-8"),
    )
    doc2 = doc_repo.create(
        title="Ghi chú ôn thi cuối kỳ Giải tích (Riêng tư)",
        description="Bản nháp tóm tắt công thức và các dạng bài tập thi Giải tích 1. Chỉ dành cho cá nhân ôn tập.",
        subject="Toán cao cấp",
        is_public=False,
        filename=fn2,
        original_filename=orig2,
        file_size=size2,
        owner_id=student_a.id,
        status="approved",
    )

    # 3. Public doc for student_b
    fn3, orig3, size3 = storage_repo.save_raw_content(
        "Slide_Lap_trinh_Web_Flask.docx",
        b"PK\x03\x04\x14\x00\x00\x00\x08\x00StudyDocs Sample DOCX Content for Flask Web Development",
    )
    doc3 = doc_repo.create(
        title="Slide bài giảng Lập trình Web với Python Flask",
        description="Tổng hợp slide bài học Flask, Jinja2 template engine, kiến trúc 3 lớp và kết nối SQLite.",
        subject="Lập trình Web",
        is_public=True,
        filename=fn3,
        original_filename=orig3,
        file_size=size3,
        owner_id=student_b.id,
        status="approved",
    )

    # 4. Private doc for student_b
    fn4, orig4, size4 = storage_repo.save_raw_content(
        "De_tai_nghien_cuu_AI.docx",
        b"PK\x03\x04\x14\x00\x00\x00\x08\x00Draft Research on AI Security and Testing",
    )
    doc4 = doc_repo.create(
        title="Đề tài nghiên cứu Khoa học cá nhân (Bản nháp)",
        description="Đề cương đề tài nghiên cứu về kiểm thử bảo mật ứng dụng web và phát hiện lỗ hổng bằng AI.",
        subject="Khoa học máy tính",
        is_public=False,
        filename=fn4,
        original_filename=orig4,
        file_size=size4,
        owner_id=student_b.id,
        status="approved",
    )

    print(f" -> Đã tạo 4 tài liệu: 2 công khai (ID={doc1.id}, ID={doc3.id}), 2 riêng tư (ID={doc2.id}, ID={doc4.id})")

    print("[*] Tạo các ghi chú/bình luận mẫu...")
    comment_repo.create(
        document_id=doc1.id,
        user_id=student_b.id,
        content="Tài liệu giải thuật rất chi tiết và dễ hiểu, cảm ơn bạn đã chia sẻ!",
    )
    comment_repo.create(
        document_id=doc1.id,
        user_id=admin.id,
        content="Tài liệu đã được duyệt và đưa vào danh mục học tập của khoa.",
    )
    comment_repo.create(
        document_id=doc3.id,
        user_id=student_a.id,
        content="Slide rất trực quan, có thêm phần thực hành mô hình MVC 3 lớp rất rõ ràng.",
    )

    conn.close()
    print("[+] Seed dữ liệu thành công hoàn tất!")
    print("\n" + "=" * 50)
    print(" DANH SÁCH TÀI KHOẢN MẪU KHỞI TẠO:")
    print("  1. Quản trị viên (admin):  admin     / Admin@123")
    print("  2. Sinh viên A:            student_a / StudentA@123")
    print("  3. Sinh viên B:            student_b / StudentB@123")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run_seed()

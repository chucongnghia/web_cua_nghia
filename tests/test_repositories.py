import pytest
import io
from werkzeug.datastructures import FileStorage


def test_user_repository_crud(repos):
    user_repo = repos["user_repo"]

    # Create user
    user = user_repo.create(
        username="test_student",
        password_hash="hash123",
        role="student",
        is_active=True,
    )
    assert user.id is not None
    assert user.username == "test_student"
    assert user.role == "student"
    assert user.is_active is True
    assert not user.is_admin()

    # Get by id and username
    by_id = user_repo.get_by_id(user.id)
    assert by_id is not None
    assert by_id.username == "test_student"

    by_name = user_repo.get_by_username("test_student")
    assert by_name is not None
    assert by_name.id == user.id

    # Update status (lock user)
    updated = user_repo.update_status(user.id, False)
    assert updated is True
    refetched = user_repo.get_by_id(user.id)
    assert refetched.is_active is False

    # List all & count
    assert user_repo.count() == 1
    users = user_repo.list_all()
    assert len(users) == 1


def test_document_repository_crud_and_search(repos):
    user_repo = repos["user_repo"]
    doc_repo = repos["doc_repo"]

    u1 = user_repo.create("alice", "hash", "student")
    u2 = user_repo.create("bob", "hash", "student")

    # Create documents
    doc_pub = doc_repo.create(
        title="Toán Rời Rạc Cơ Bản",
        description="Lý thuyết đồ thị và tổ hợp",
        subject="Toán học",
        is_public=True,
        filename="d1.pdf",
        original_filename="toan.pdf",
        file_size=1024,
        owner_id=u1.id,
    )

    doc_priv = doc_repo.create(
        title="Ghi chú cá nhân Bob",
        description="Bí mật ôn thi",
        subject="Lập trình",
        is_public=False,
        filename="d2.txt",
        original_filename="note.txt",
        file_size=512,
        owner_id=u2.id,
    )

    # Search as unauthenticated / public
    public_docs = doc_repo.search(user_id=None, is_admin=False)
    assert len(public_docs) == 1
    assert public_docs[0].id == doc_pub.id

    # Search as Alice (owner of doc_pub): cannot see Bob's private doc
    alice_docs = doc_repo.search(user_id=u1.id, is_admin=False)
    assert len(alice_docs) == 1

    # Search as Bob: can see public doc and own private doc
    bob_docs = doc_repo.search(user_id=u2.id, is_admin=False)
    assert len(bob_docs) == 2

    # Search as Admin: can see all docs
    admin_docs = doc_repo.search(is_admin=True)
    assert len(admin_docs) == 2

    # Keyword search
    res = doc_repo.search(keyword="Đồ thị", is_admin=True)
    assert len(res) == 1
    assert res[0].id == doc_pub.id

    # Filter by subject
    res_subj = doc_repo.search(subject="Lập trình", is_admin=True)
    assert len(res_subj) == 1
    assert res_subj[0].id == doc_priv.id

    # Update document
    doc_repo.update(
        doc_id=doc_pub.id,
        title="Toán Rời Rạc Nâng Cao",
        description="Bổ sung giải thuật",
        subject="Toán học",
        is_public=True,
    )
    updated = doc_repo.get_by_id(doc_pub.id)
    assert updated.title == "Toán Rời Rạc Nâng Cao"

    # Delete document
    deleted = doc_repo.delete(doc_pub.id)
    assert deleted is True
    assert doc_repo.get_by_id(doc_pub.id) is None


def test_comment_repository(repos):
    user_repo = repos["user_repo"]
    doc_repo = repos["doc_repo"]
    comment_repo = repos["comment_repo"]

    u = user_repo.create("alice", "hash", "student")
    doc = doc_repo.create(
        title="Doc 1",
        description="",
        subject="IT",
        is_public=True,
        filename="f.pdf",
        original_filename="f.pdf",
        file_size=10,
        owner_id=u.id,
    )

    c = comment_repo.create(
        document_id=doc.id, user_id=u.id, content="Tài liệu hay lắm"
    )
    assert c.id is not None
    assert c.content == "Tài liệu hay lắm"

    comments = comment_repo.list_by_document(doc.id)
    assert len(comments) == 1
    assert comments[0].author_username == "alice"


def test_storage_repository(repos):
    storage = repos["storage_repo"]

    # Allowed extensions
    assert storage.is_allowed_file("document.pdf") is True
    assert storage.is_allowed_file("notes.docx") is True
    assert storage.is_allowed_file("readme.txt") is True
    assert storage.is_allowed_file("script.exe") is False
    assert storage.is_allowed_file("shell.php") is False

    # Save file storage
    file_bytes = b"Hello StudyDocs test file content"
    stream = io.BytesIO(file_bytes)
    fs = FileStorage(stream=stream, filename="lecture.pdf")

    saved_fn, orig_fn, size = storage.save_file(fs)
    assert orig_fn == "lecture.pdf"
    assert size == len(file_bytes)
    assert storage.file_exists(saved_fn) is True

    # Path traversal protection
    assert storage.get_file_path("../../windows/win.ini") is None
    assert storage.get_file_path("..\\..\\windows\\system32\\cmd.exe") is None

    # Delete file
    assert storage.delete_file(saved_fn) is True
    assert storage.file_exists(saved_fn) is False

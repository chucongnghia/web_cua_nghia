import os
import shutil
import tempfile
import sqlite3
import pytest
from app import create_app
from app.config import TestingConfig
from app.repositories.db import init_db
from app.repositories.user_repository import UserRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.comment_repository import CommentRepository
from app.repositories.storage_repository import StorageRepository
from werkzeug.security import generate_password_hash


@pytest.fixture
def temp_dir():
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def test_db_conn():
    from app.repositories.db import connect_db
    conn = connect_db(":memory:")
    init_db(conn)
    yield conn
    conn.close()


@pytest.fixture
def app(temp_dir):
    test_db_path = os.path.join(temp_dir, "test.db")
    upload_path = os.path.join(temp_dir, "uploads")
    log_path = os.path.join(temp_dir, "test.log")

    class CustomTestConfig(TestingConfig):
        DATABASE_PATH = test_db_path
        UPLOAD_FOLDER = upload_path
        LOG_FILE = log_path
        SECRET_KEY = "test-secret"
        TESTING = True

    app = create_app(CustomTestConfig)
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def repos(test_db_conn, temp_dir):
    user_repo = UserRepository(test_db_conn)
    doc_repo = DocumentRepository(test_db_conn)
    comment_repo = CommentRepository(test_db_conn)
    storage_repo = StorageRepository(temp_dir)
    return {
        "user_repo": user_repo,
        "doc_repo": doc_repo,
        "comment_repo": comment_repo,
        "storage_repo": storage_repo,
        "conn": test_db_conn,
    }

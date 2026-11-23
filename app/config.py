import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "studydocs-v0-dev-secret-key-safe-2026")
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
    LOG_FILE = os.path.join(BASE_DIR, "app.log")
    DATABASE_PATH = os.path.join(BASE_DIR, "studydocs.db")
    TESTING = False
    DEBUG = False


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = False
    DATABASE_PATH = ":memory:"
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "tests", "test_uploads")
    LOG_FILE = os.path.join(BASE_DIR, "tests", "test_app.log")


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}

from app.routes.auth_routes import auth_bp
from app.routes.document_routes import document_bp
from app.routes.admin_routes import admin_bp
from app.routes.user_routes import user_bp

__all__ = ["auth_bp", "document_bp", "admin_bp", "user_bp"]

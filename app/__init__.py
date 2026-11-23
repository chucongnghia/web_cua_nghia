import os
from flask import Flask
from app.config import config_by_name, BaseConfig
from app.repositories.db import init_db, close_db
from app.routes.common import get_current_user
from app.routes import auth_bp, document_bp, admin_bp, user_bp
from app.services.logger_service import get_activity_logger


def create_app(config_name_or_obj=None):
    app = Flask(__name__)

    # Load configuration
    if isinstance(config_name_or_obj, str):
        config_cls = config_by_name.get(config_name_or_obj, BaseConfig)
        app.config.from_object(config_cls)
    elif config_name_or_obj is not None:
        app.config.from_object(config_name_or_obj)
    else:
        env = os.environ.get("FLASK_ENV", "development")
        app.config.from_object(config_by_name.get(env, BaseConfig))

    # Ensure upload directory exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize SQLite database schema
    init_db(app.config["DATABASE_PATH"])

    # Setup logger
    with app.app_context():
        get_activity_logger(app.config.get("LOG_FILE"))

    # Register teardown
    app.teardown_appcontext(close_db)

    # Inject current_user into templates
    @app.context_processor
    def inject_user():
        return {"current_user": get_current_user()}

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(document_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)

    return app

# app/__init__.py
import os
from flask import Flask
from .extensions import db, limiter  # <-- shared singletons

def create_app():
    app = Flask(__name__)

    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", f"sqlite:///{db_path}")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")

    # Initialize extensions
    db.init_app(app)
    limiter.init_app(app)

    with app.app_context():
        db.create_all()
        from .routes import bp as routes_bp
        app.register_blueprint(routes_bp)

    return app

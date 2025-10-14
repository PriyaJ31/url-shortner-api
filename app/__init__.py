import os
from flask import Flask
from .models import db  # imports the SQLAlchemy instance

def create_app():
    app = Flask(__name__)

    # SQLite file in project root: database.db (default)
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", f"sqlite:///{db_path}")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")

    db.init_app(app)

    with app.app_context():
        # Creates tables once (no-op on subsequent runs)
        db.create_all()

        from .routes import bp as routes_bp
        app.register_blueprint(routes_bp)  # root: /shorten, /<short_id>, /all

    return app

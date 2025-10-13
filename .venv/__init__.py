from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)

    with app.app_context():
        # Import models to register them and create tables
        from .models import URL  # noqa: F401
        db.create_all()

        from .routes import bp as routes_bp
        app.register_blueprint(routes_bp)

    return app

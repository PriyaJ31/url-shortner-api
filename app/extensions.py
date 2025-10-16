# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Singletons used across the app
db = SQLAlchemy()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],       # no global default; we’ll decorate specific routes
    storage_uri="memory://", # in-memory, no external service
)

from datetime import datetime
from . import db

class URL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(2048), unique=True, nullable=False, index=True)  # unique to detect duplicates
    short_id = db.Column(db.String(16), unique=True, index=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # analytics
    click_count = db.Column(db.Integer, default=0, nullable=False)
    last_accessed = db.Column(db.DateTime, nullable=True)

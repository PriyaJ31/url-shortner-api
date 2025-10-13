from flask import Blueprint, request, jsonify, redirect, render_template_string
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from urllib.parse import urlparse
from . import db
from .models import URL
import string, random

bp = Blueprint("routes", __name__)

def _generate_short_id(k=6):
    alphabet = string.ascii_letters + string.digits
    return ''.join(random.choices(alphabet, k=k))

def _is_valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False

@bp.app_errorhandler(404)
def handle_404(e):
    # JSON for API paths, simple text for browser
    if request.accept_mimetypes["application/json"] >= request.accept_mimetypes["text/html"]:
        return jsonify(error="Not Found", path=request.path), 404
    return "Not Found", 404

@bp.app_errorhandler(400)
def handle_400(e):
    return jsonify(error="Bad Request", detail=str(e)), 400

@bp.route("/", methods=["GET"])
def home():
    # Minimal homepage form
    return render_template_string("""
    <html>
    <head>
        <title>URL Shortener</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; margin-top: 100px; }
            input[type=url] { width: 360px; padding: 10px; }
            button { padding: 10px 20px; margin-left: 8px; }
            .msg { margin-top: 16px; }
        </style>
    </head>
    <body>
        <h2>Shorten your URL</h2>
        <form method="POST" action="/shorten">
            <input type="url" name="url" placeholder="https://example.com" required>
            <button type="submit">Shorten</button>
        </form>
        <p class="msg">POST /shorten with JSON or form field <code>url</code>.</p>
    </body>
    </html>
    """)

@bp.route("/shorten", methods=["POST"])
def shorten():
    data = request.get_json(silent=True) or request.form
    original_url = (data.get("url") or data.get("original_url") or "").strip()

    # invalid / missing input
    if not original_url:
        return jsonify({"error": "Missing 'url' in body"}), 400
    if not _is_valid_url(original_url):
        return jsonify({"error": "Invalid URL. Use http(s)://..."}), 400

    # if URL already exists, return existing short link (no error)
    existing = URL.query.filter_by(original_url=original_url).first()
    if existing:
        short_url = request.host_url + existing.short_id
        return jsonify({
            "message": "URL already shortened",
            "duplicate": True,
            "short_id": existing.short_id,
            "short_url": short_url,
            "original_url": existing.original_url
        }), 200

    # generate unique short_id
    short_id = None
    for _ in range(7):  # a few attempts
        candidate = _generate_short_id(6)
        if not URL.query.filter_by(short_id=candidate).first():
            short_id = candidate
            break
    if not short_id:
        return jsonify({"error": "Could not generate unique short id"}), 500

    # create row
    url_row = URL(original_url=original_url, short_id=short_id)
    db.session.add(url_row)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # Rare race: if another request inserted same original_url first
        existing = URL.query.filter_by(original_url=original_url).first()
        short_url = request.host_url + existing.short_id
        return jsonify({
            "message": "URL already shortened",
            "duplicate": True,
            "short_id": existing.short_id,
            "short_url": short_url,
            "original_url": existing.original_url
        }), 200

    short_url = request.host_url + short_id
    print(f"[INFO] Short URL created: {short_url} -> {original_url}")
    return jsonify({
        "short_id": short_id,
        "short_url": short_url,
        "original_url": original_url
    }), 201

@bp.route("/<string:short_id>", methods=["GET"])
def redirect_short(short_id):
    row = URL.query.filter_by(short_id=short_id).first()
    if not row:
        return jsonify({"error": "Not found"}), 404

    # update analytics
    row.click_count = (row.click_count or 0) + 1
    row.last_accessed = datetime.utcnow()
    db.session.commit()

    return redirect(row.original_url, code=302)

# (Optional) quick stats endpoint for testing analytics
@bp.route("/stats/<string:short_id>", methods=["GET"])
def stats(short_id):
    row = URL.query.filter_by(short_id=short_id).first()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify({
        "short_id": row.short_id,
        "original_url": row.original_url,
        "created_at": row.created_at.isoformat() + "Z",
        "click_count": row.click_count,
        "last_accessed": row.last_accessed.isoformat() + "Z" if row.last_accessed else None
    })

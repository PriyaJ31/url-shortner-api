from flask import Blueprint, request, jsonify, redirect, render_template, render_template_string
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from urllib.parse import urlparse
import string, random

from .models import db, URL
from .extensions import limiter  # rate limiter singleton

bp = Blueprint("routes", __name__)

# ----------------------
# Helpers
# ----------------------
def error_response(message: str, status: int = 400, hint: str | None = None):
    payload = {"error": message}
    if hint:
        payload["hint"] = hint
    return jsonify(payload), status

def _generate_short_id(k=6):
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choices(alphabet, k=k))

def _is_valid_url(url: str) -> bool:
    """Strict-ish check without extra deps: require http(s), netloc, no spaces."""
    if not url or not isinstance(url, str) or url.strip() == "":
        return False
    if " " in url:
        return False
    try:
        p = urlparse(url)
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False

# ----------------------
# Error handlers (JSON shape unified)
# ----------------------
@bp.app_errorhandler(404)
def handle_404(e):
    return error_response("Not Found", 404, hint="Check the path or short_id.")

@bp.app_errorhandler(400)
def handle_400(e):
    return error_response("Bad Request", 400, hint=str(e))

# ----------------------
# Home page (simple form)
# ----------------------
@bp.route("/", methods=["GET"], endpoint="home_page")
def home():
    return render_template_string("""
    <html>
    <head>
        <title>URL Shortener</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; margin-top: 100px; }
            input[type=url] { width: 360px; padding: 10px; }
            button { padding: 10px 20px; margin-left: 8px; }
            .msg { margin-top: 16px; color: #666; }
        </style>
    </head>
    <body>
        <h2>🔗 URL Shortener</h2>
        <form method="POST" action="/shorten">
            <input type="url" name="url" placeholder="https://example.com" required>
            <button type="submit">Shorten</button>
        </form>
        <p class="msg">Use <code>POST /shorten</code> (JSON or form) to create a short link. View stats at <a href="/analytics">/analytics</a>.</p>
    </body>
    </html>
    """)

# ----------------------
# Create short URL (validation + consistent errors + rate limit)
# ----------------------
@bp.route("/shorten", methods=["POST"], endpoint="shorten_url")
@limiter.limit("5 per minute")   # 5 req/min per client IP
def shorten():
    data = request.get_json(silent=True) or request.form
    original_url = (data.get("url") or data.get("original_url") or "").strip()

    if not original_url:
        return error_response("Missing 'url'", 400, hint='Send JSON: {"url": "https://..."}')
    if not _is_valid_url(original_url):
        return error_response("Invalid URL", 400, hint="Use http(s):// and a valid host.")

    # Return existing mapping if present (duplicate handling)
    existing = URL.query.filter_by(original_url=original_url).first()
    if existing:
        short_url = request.host_url + existing.short_id
        # Browser form UX: show clickable link
        if not request.is_json:
            return render_template_string(f"""
            <p>✅ Already shortened:</p>
            <p><a href="{short_url}">{short_url}</a></p>
            <p><a href="/">Create another</a></p>
            """), 200
        return jsonify({
            "message": "URL already shortened",
            "duplicate": True,
            "short_id": existing.short_id,
            "short_url": short_url,
            "original_url": existing.original_url
        }), 200

    # Generate unique short_id
    short_id = None
    for _ in range(7):
        cand = _generate_short_id(6)
        if not URL.query.filter_by(short_id=cand).first():
            short_id = cand
            break
    if not short_id:
        return error_response("Could not generate unique short id", 500)

    # Persist
    row = URL(original_url=original_url, short_id=short_id)
    db.session.add(row)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # Extremely rare: collision or concurrent insert
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
        return error_response("Database error", 500, hint="Please retry.")

    short_url = request.host_url + short_id
    print(f"[INFO] Short URL created: {short_url} -> {original_url}")  # console log for local testing

    # If submitted from the browser form, show a small success page
    if not request.is_json:
        return render_template_string(f"""
        <p>✅ Short URL created:</p>
        <p><a href="{short_url}">{short_url}</a></p>
        <p><a href="/">Create another</a></p>
        """), 201

    return jsonify({
        "short_id": short_id,
        "short_url": short_url,
        "original_url": original_url
    }), 201

# ----------------------
# Redirect by short_id (+analytics)
# ----------------------
@bp.route("/<string:short_id>", methods=["GET"], endpoint="redirect_short")
def redirect_short(short_id):
    row = URL.query.filter_by(short_id=short_id).first()
    if not row:
        return error_response("Not Found", 404, hint="Unknown short_id.")

    # Update analytics
    try:
        row.click_count = (row.click_count or 0) + 1
        if hasattr(row, "last_accessed"):
            row.last_accessed = datetime.utcnow()
        db.session.commit()
    except Exception:
        db.session.rollback()  # don't block redirect on analytics error
    return redirect(row.original_url, code=302)

# ----------------------
# List all entries (JSON)
# ----------------------
@bp.route("/all", methods=["GET"], endpoint="list_all_urls")
def list_all():
    rows = URL.query.order_by(URL.id.desc()).all()
    payload = []
    for r in rows:
        item = {
            "id": r.id,
            "original_url": r.original_url,
            "short_id": r.short_id,
            "click_count": r.click_count,
            "created_at": r.created_at.isoformat() + "Z" if r.created_at else None,
        }
        if hasattr(r, "last_accessed") and r.last_accessed:
            item["last_accessed"] = r.last_accessed.isoformat() + "Z"
        payload.append(item)
    return jsonify(payload), 200

# ----------------------
# Quick stats for one entry (JSON)
# ----------------------
@bp.route("/stats/<string:short_id>", methods=["GET"], endpoint="stats_one")
def stats(short_id):
    r = URL.query.filter_by(short_id=short_id).first()
    if not r:
        return error_response("Not Found", 404, hint="Unknown short_id.")
    item = {
        "id": r.id,
        "original_url": r.original_url,
        "short_id": r.short_id,
        "click_count": r.click_count,
        "created_at": r.created_at.isoformat() + "Z" if r.created_at else None,
    }
    if hasattr(r, "last_accessed") and r.last_accessed:
        item["last_accessed"] = r.last_accessed.isoformat() + "Z"
    return jsonify(item), 200

# ----------------------
# Analytics UI (HTML)
# ----------------------
@bp.route("/analytics", methods=["GET"], endpoint="analytics_page")
def analytics_page():
    q = (request.args.get("q") or "").strip()
    query = URL.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            (URL.original_url.ilike(like)) | (URL.short_id.ilike(like))
        )

    rows = query.order_by(URL.click_count.desc(), URL.id.desc()).all()

    # top 10 for chart
    top = rows[:10]
    labels = [r.short_id for r in top]
    clicks = [r.click_count for r in top]

    return render_template(
        "analytics.html",
        rows=rows,
        q=q,
        labels=labels,
        clicks=clicks,
    )

# ----------------------
# Analytics JSON (programmatic)
# ----------------------
@bp.route("/api/analytics", methods=["GET"], endpoint="analytics_json")
def analytics_json():
    q = (request.args.get("q") or "").strip()
    query = URL.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            (URL.original_url.ilike(like)) | (URL.short_id.ilike(like))
        )
    rows = query.order_by(URL.click_count.desc(), URL.id.desc()).all()
    payload = []
    for r in rows:
        item = {
            "short_id": r.short_id,
            "original_url": r.original_url,
            "click_count": r.click_count,
            "created_at": r.created_at.isoformat() + "Z" if r.created_at else None,
        }
        if hasattr(r, "last_accessed") and r.last_accessed:
            item["last_accessed"] = r.last_accessed.isoformat() + "Z"
        payload.append(item)
    return jsonify(payload), 200

from flask import Blueprint, request, jsonify, redirect
from datetime import datetime
from urllib.parse import urlparse
from sqlalchemy.exc import IntegrityError
import string, random

from .models import db, URL

bp = Blueprint("routes", __name__)

def _generate_short_id(k=6):
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choices(alphabet, k=k))

def _is_valid_url(url: str) -> bool:
    try:
        p = urlparse(url)
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False

@bp.route("/shorten", methods=["POST"])
def shorten():
    data = request.get_json(silent=True) or request.form
    original_url = (data.get("url") or data.get("original_url") or "").strip()

    if not original_url:
        return jsonify({"error": "Missing 'url'"}), 400
    if not _is_valid_url(original_url):
        return jsonify({"error": "Invalid URL. Use http(s)://..."}), 400

    # Optional: return existing entry for same original_url (not unique at DB level)
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

    # ensure unique short_id
    short_id = None
    for _ in range(7):
        cand = _generate_short_id(6)  # <= 10 chars allowed by column
        if not URL.query.filter_by(short_id=cand).first():
            short_id = cand
            break
    if not short_id:
        return jsonify({"error": "Could not generate unique short id"}), 500

    row = URL(original_url=original_url, short_id=short_id)
    db.session.add(row)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Collision on short id, try again"}), 500

    short_url = request.host_url + short_id
    print(f"[INFO] Short URL created: {short_url} -> {original_url}")  # console print for local test

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

    row.click_count += 1
    db.session.commit()
    return redirect(row.original_url, code=302)

@bp.route("/all", methods=["GET"])
def list_all():
    rows = URL.query.order_by(URL.id.desc()).all()
    return jsonify([r.to_dict() for r in rows])

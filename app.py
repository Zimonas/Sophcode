import os
import json
import requests
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response
from werkzeug.security import check_password_hash
from datetime import timedelta
import psycopg2
import psycopg2.extras

app = Flask(__name__)

# --- CONFIG ---
app.secret_key = os.environ.get("SECRET_KEY", "dev_fallback")
app.permanent_session_lifetime = timedelta(days=7)

ADMIN_USER = os.environ.get("ADMIN_USER", "MasterZanix")
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH")

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

DATABASE_URL = os.environ.get("DATABASE_URL")

# --- DATABASE HELPERS ---
def get_db():
    return psycopg2.connect(
        DATABASE_URL,
        sslmode="require",
        cursor_factory=psycopg2.extras.DictCursor
    )

def init_db():
    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS codes (
                    id SERIAL PRIMARY KEY,
                    code TEXT UNIQUE NOT NULL,
                    clicks INTEGER DEFAULT 0
                )
            """)
        con.commit()

init_db()

# --- TELEGRAM ---
def send_tg(code: str):
    if not TG_TOKEN or not TG_CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={
                "chat_id": TG_CHAT_ID,
                "text": f"🚀 *New Copy Detected!*\n\nCode: `{code}`",
                "parse_mode": "Markdown"
            },
            timeout=5
        )
    except:
        pass

# --- SEO ROUTES ---
@app.route("/robots.txt")
def robots():
    return Response(
        "User-agent: *\nDisallow: /manage-zemy-codes\nDisallow: /add\nDisallow: /delete\nSitemap: https://sophiapromo.codes/sitemap.xml\n",
        mimetype="text/plain",
    )

@app.route("/sitemap.xml")
def sitemap():
    # Dynamic sitemap (optional) - for now static is enough for index
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://sophiapromo.codes/</loc>
    <changefreq>hourly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
"""
    return Response(xml, mimetype="application/xml")

# --- API (for live counters) ---
@app.route("/api/codes")
def api_codes():
    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("SELECT id, code, clicks FROM codes ORDER BY id DESC")
            rows = cur.fetchall()
    return jsonify([dict(r) for r in rows])

# --- ROUTES ---
@app.route("/")
def index():
    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("SELECT id, code, clicks FROM codes ORDER BY id DESC")
            codes = cur.fetchall()
    return render_template("index.html", codes=codes)

@app.route("/track-copy", methods=["POST"])
def track_copy():
    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip()
    if not code:
        return "", 400

    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("UPDATE codes SET clicks = clicks + 1 WHERE code = %s", (code,))
        con.commit()

    send_tg(code)
    return "", 204

@app.route("/manage-zemy-codes", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if (
            request.form.get("username") == ADMIN_USER
            and ADMIN_PASSWORD_HASH
            and check_password_hash(ADMIN_PASSWORD_HASH, request.form.get("password"))
        ):
            session["logged_in"] = True
            session.permanent = True
            return redirect(url_for("admin"))

    if not session.get("logged_in"):
        return render_template("login.html")

    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("SELECT id, code, clicks FROM codes ORDER BY id DESC")
            codes = cur.fetchall()

    return render_template("admin.html", codes=codes)

@app.route("/add", methods=["POST"])
def add():
    if not session.get("logged_in"):
        return redirect(url_for("admin"))

    raw = request.form.get("bulk_codes", "")
    incoming = [c.strip() for c in raw.splitlines() if c.strip()]

    with get_db() as con:
        with con.cursor() as cur:
            for c in incoming:
                cur.execute(
                    "INSERT INTO codes (code) VALUES (%s) ON CONFLICT DO NOTHING",
                    (c,)
                )
        con.commit()

    return redirect(url_for("admin"))

@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    if not session.get("logged_in"):
        return redirect(url_for("admin"))

    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("DELETE FROM codes WHERE id = %s", (id,))
        con.commit()

    return redirect(url_for("admin"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

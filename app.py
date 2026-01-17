import os
import requests
import secrets
from time import time
from datetime import timedelta, date
import psycopg2
import psycopg2.extras
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response
from werkzeug.security import check_password_hash

app = Flask(__name__)

# --- CONFIG ---
app.secret_key = os.environ.get('SECRET_KEY', 'devfallback')
app.permanent_session_lifetime = timedelta(days=7)

ADMIN_USER = os.environ.get('ADMIN_USER', 'MasterZanix')
ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH')

TG_TOKEN = os.environ.get('TG_TOKEN')
TG_CHAT_ID = os.environ.get('TG_CHAT_ID')
DATABASE_URL = os.environ.get('DATABASE_URL')

# --- DATABASE ---
def get_db():
    return psycopg2.connect(
        DATABASE_URL,
        sslmode='require',
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

try:
    init_db()
except Exception as e:
    print(f"DB init warning: {e}")

# --- SEO CACHING ---
@app.after_request
def add_headers(response):
    if (
        request.path == '/' or
        request.path.startswith('/sophia') or
        request.path == '/sitemap.xml'
    ):
        response.headers['Cache-Control'] = 'public, max-age=600'
    return response

# --- TELEGRAM ---
def send_tg_code(code: str):
    if not TG_TOKEN or not TG_CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={
                "chat_id": TG_CHAT_ID,
                "text": f"🚀 New Copy Detected!\n\nCode: `{code}`"
            },
            timeout=5
        )
    except Exception:
        pass

# --- ROBOTS ---
@app.route('/robots.txt')
def robots():
    txt = """User-agent: *
Disallow: /manage-zemy-codes
Disallow: /add
Disallow: /delete

Sitemap: https://sophiapromo.codes/sitemap.xml
"""
    return Response(txt, mimetype='text/plain')

# --- SITEMAP ---
@app.route('/sitemap.xml')
def sitemap():
    base_url = "https://sophiapromo.codes"
    today = date.today().isoformat()

    pages = [
        '/',
        '/sophia-referral-code-not-working',
        '/sophia-learning-vs-study-com-cost',
        '/how-to-use-sophia-referral-code',
        '/sophia-learning-discount-existing-members',
        '/sophia-code-stats'
    ]

    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    for p in pages:
        priority = '1.0' if p == '/' else '0.8'
        freq = 'daily' if p == '/sophia-code-stats' else 'weekly'
        xml.append(
            f'<url>'
            f'<loc>{base_url}{p}</loc>'
            f'<lastmod>{today}</lastmod>'
            f'<changefreq>{freq}</changefreq>'
            f'<priority>{priority}</priority>'
            f'</url>'
        )

    xml.append('</urlset>')
    return Response(''.join(xml), mimetype='application/xml')

# --- INDEXNOW KEY ---
@app.route('/4024e745f5874cd799c12a56802f6a24.txt')
def indexnow_key():
    return Response('4024e745f5874cd799c12a56802f6a24', mimetype='text/plain')

# --- API (NOINDEX) ---
@app.route('/api/codes')
def api_codes():
    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("SELECT id, code, clicks FROM codes ORDER BY id DESC")
            rows = cur.fetchall()

    response = jsonify([dict(r) for r in rows])
    response.headers['X-Robots-Tag'] = 'noindex'
    return response

# --- RATE LIMIT (COPY TRACKING) ---
COPY_RATE = {}

@app.route('/track-copy', methods=['POST'])
def track_copy():
    ip = request.remote_addr
    now = time()

    if ip in COPY_RATE and now - COPY_RATE[ip] < 1.5:
        return "", 429

    COPY_RATE[ip] = now

    data = request.get_json(silent=True) or {}
    code = data.get('code', '').strip()
    if not code:
        return "", 400

    with get_db() as con:
        with con.cursor() as cur:
            cur.execute(
                "UPDATE codes SET clicks = clicks + 1 WHERE code = %s",
                (code,)
            )
        con.commit()

    send_tg_code(code)
    return "", 204

# --- PUBLIC ---
@app.route('/')
def index():
    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("SELECT id, code, clicks FROM codes ORDER BY id DESC")
            codes = cur.fetchall()
    return render_template('index.html', codes=codes)

# --- SEO PAGES ---
@app.route('/sophia-referral-code-not-working')
def not_working():
    return render_template('not_working.html')

@app.route('/sophia-learning-vs-study-com-cost')
def comparison():
    return render_template('comparison.html')

@app.route('/how-to-use-sophia-referral-code')
def how_to():
    return render_template('how_to.html')

@app.route('/sophia-learning-discount-existing-members')
def existing_members():
    return render_template('existing_members.html')

@app.route('/sophia-code-stats')
def stats():
    try:
        with get_db() as con:
            with con.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM codes")
                total_codes = cur.fetchone()[0]

                cur.execute("SELECT SUM(clicks) FROM codes")
                total_clicks = cur.fetchone()[0] or 0

                cur.execute(
                    "SELECT code, clicks FROM codes ORDER BY clicks DESC LIMIT 1"
                )
                top = cur.fetchone() or ("None", 0)

        return render_template(
            'stats.html',
            total_codes=total_codes,
            total_clicks=total_clicks,
            top_code=top
        )
    except Exception:
        return render_template(
            'stats.html',
            total_codes=0,
            total_clicks=0,
            top_code=("None", 0)
        )

# --- ADMIN (CSRF + BRUTE FORCE) ---
@app.route('/manage-zemy-codes', methods=['GET', 'POST'])
def admin():
    if not session.get('csrf'):
        session['csrf'] = secrets.token_hex(16)

    if request.method == 'POST':
        if request.form.get('csrf') != session.get('csrf'):
            return "Invalid CSRF token", 400

        session['attempts'] = session.get('attempts', 0) + 1
        if session['attempts'] > 10:
            return "Too many attempts", 429

        if (
            request.form.get('username') == ADMIN_USER and
            check_password_hash(
                ADMIN_PASSWORD_HASH,
                request.form.get('password')
            )
        ):
            session['loggedin'] = True
            session.permanent = True
            session.pop('attempts', None)
            return redirect(url_for('admin'))

    if not session.get('loggedin'):
        return render_template('login.html')

    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("SELECT id, code, clicks FROM codes ORDER BY id DESC")
            codes = cur.fetchall()

    return render_template('admin.html', codes=codes)

@app.route('/add', methods=['POST'])
def add():
    if not session.get('loggedin'):
        return redirect(url_for('admin'))

    raw = request.form.get('bulkcodes', '')
    incoming = [c.strip() for c in raw.splitlines() if c.strip()]

    with get_db() as con:
        with con.cursor() as cur:
            for c in incoming:
                cur.execute(
                    "INSERT INTO codes (code) VALUES (%s) ON CONFLICT DO NOTHING",
                    (c,)
                )
        con.commit()

    return redirect(url_for('admin'))

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    if not session.get('loggedin'):
        return redirect(url_for('admin'))

    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("DELETE FROM codes WHERE id = %s", (id,))
        con.commit()

    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

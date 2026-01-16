import os
import requests
from datetime import timedelta
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
# Ensure you set this hash env var. Example hash for 'password': 
# pbkdf2:sha256:600000$....

TG_TOKEN = os.environ.get('TG_TOKEN')
TG_CHAT_ID = os.environ.get('TG_CHAT_ID')
DATABASE_URL = os.environ.get('DATABASE_URL')

# --- DATABASE HELPERS ---
def get_db():
    return psycopg2.connect(DATABASE_URL, sslmode='require', cursor_factory=psycopg2.extras.DictCursor)

def init_db():
    """Run this once manually or on startup if needed to create table"""
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

# Initialize DB on start (optional, safe to leave if table exists)
try:
    init_db()
except Exception as e:
    print(f"DB Init Warning: {e}")

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

# --- SEO ROUTES ---

@app.route('/robots.txt')
def robots():
    txt = """User-agent: *
Disallow: /manage-zemy-codes
Disallow: /add
Disallow: /delete

Sitemap: https://sophiapromo.codes/sitemap.xml
"""
    return Response(txt, mimetype='text/plain')

@app.route('/sitemap.xml')
def sitemap():
    base_url = "https://sophiapromo.codes"
    
    # 1. Define your pages (The Home + The 5 New SEO Pages)
    pages = [
        '/',
        '/sophia-referral-code-not-working',        # Troubleshooting Intent
        '/sophia-learning-vs-study-com-cost',       # Comparison Intent
        '/how-to-use-sophia-referral-code',         # Instructional Intent
        '/sophia-learning-discount-existing-members', # Specific Audience Intent
        '/sophia-code-stats'                        # "Be The Source" Link-building Page
    ]
    
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    for p in pages:
        # Homepage gets 1.0 priority, others 0.8
        priority = '1.0' if p == '/' else '0.8'
        # Stats page changes daily (live data), others weekly
        freq = 'daily' if p == '/sophia-code-stats' else 'weekly'
        
        xml.append(f'<url><loc>{base_url}{p}</loc><changefreq>{freq}</changefreq><priority>{priority}</priority></url>')
        
    xml.append('</urlset>')
    return Response(''.join(xml), mimetype='application/xml')

# --- BING INDEXNOW VERIFICATION ---
# This serves the key file at: https://sophiapromo.codes/3d8df41a04bf46bfa12553d9e1e068d6.txt
@app.route('/3d8df41a04bf46bfa12553d9e1e068d6.txt')
def indexnow_key():
    return Response('3d8df41a04bf46bfa12553d9e1e068d6', mimetype='text/plain')


# --- API for live counters ---
@app.route('/api/codes')
def api_codes():
    """Returns JSON for client-side live updates"""
    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("SELECT id, code, clicks FROM codes ORDER BY id DESC")
            rows = cur.fetchall()
    return jsonify([dict(r) for r in rows])


# --- MAIN PUBLIC ROUTES ---

@app.route('/')
def index():
    """The Main Homepage - Target: 'Sophia Promo Codes'"""
    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("SELECT id, code, clicks FROM codes ORDER BY id DESC")
            codes = cur.fetchall()
    return render_template('index.html', codes=codes)

@app.route('/track-copy', methods=['POST'])
def track_copy():
    """Increments click count when user copies a code"""
    data = request.get_json(silent=True) or {}
    code = data.get('code', '').strip()
    
    if not code:
        return "", 400

    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("UPDATE codes SET clicks = clicks + 1 WHERE code = %s", (code,))
        con.commit()
    
    # Notify Admin via Telegram
    send_tg_code(code)
    
    return "", 204

# --- NEW SEO TARGET PAGES (Create these HTML files in /templates) ---

@app.route('/sophia-referral-code-not-working')
def not_working():
    """Target: Troubleshooting keywords (Low competition)"""
    return render_template('not_working.html')

@app.route('/sophia-learning-vs-study-com-cost')
def comparison():
    """Target: 'Sophia vs Study.com' (Comparison intent)"""
    return render_template('comparison.html')

@app.route('/how-to-use-sophia-referral-code')
def how_to():
    """Target: Instructional keywords"""
    return render_template('how_to.html')

@app.route('/sophia-learning-discount-existing-members')
def existing_members():
    """Target: Specific niche query"""
    return render_template('existing_members.html')

@app.route('/sophia-code-stats')
def stats():
    """
    Target: 'Sophia Learning Statistics' / Link Building Asset
    This page uses DB data to show 'Real Success Rates', making you a source.
    """
    try:
        with get_db() as con:
            with con.cursor() as cur:
                # 1. Total Codes Tracked
                cur.execute("SELECT COUNT(*) FROM codes")
                count_res = cur.fetchone()
                total_codes = count_res[0] if count_res else 0
                
                # 2. Total Clicks (Proxy for success/usage)
                cur.execute("SELECT SUM(clicks) FROM codes")
                click_res = cur.fetchone()
                total_clicks = click_res[0] if click_res and click_res[0] else 0
                
                # 3. Most Popular Code (For 'Top Trending' stat)
                cur.execute("SELECT code, clicks FROM codes ORDER BY clicks DESC LIMIT 1")
                top_res = cur.fetchone()
                top_code = top_res if top_res else ("None", 0)

        return render_template('stats.html', 
                             total_codes=total_codes, 
                             total_clicks=total_clicks, 
                             top_code=top_code)
    except Exception as e:
        # Fail gracefully if DB issues occur
        return render_template('stats.html', total_codes=0, total_clicks=0, top_code=("None", 0))


# --- ADMIN ROUTES ---

@app.route('/manage-zemy-codes', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if (request.form.get('username') == ADMIN_USER and 
            check_password_hash(ADMIN_PASSWORD_HASH, request.form.get('password'))):
            session['loggedin'] = True
            session.permanent = True
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
                cur.execute("INSERT INTO codes (code) VALUES (%s) ON CONFLICT DO NOTHING", (c,))
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

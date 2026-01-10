import os, json, time, requests
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "zemy_ultra_secure_2026" 
app.permanent_session_lifetime = timedelta(days=7)

# --- CONFIGURATION ---
ADMIN_USER = "MasterZanix"
ADMIN_PASSWORD_HASH = "scrypt:32768:8:1$mCa1VowXKLSWJEYy$45b2f9e646b1b65bb75ab849227e86018d91bb30ad6bbeab513fe2a944c5876d4e25c2e23fdffc3478b560ab43ab81966ef0eeec755b9b9c87c8d51f25219448"
DATA_FILE = 'codes.json'

# --- TELEGRAM CONFIG ---
TG_TOKEN = "5655120748:AAGK-LjVuPqksciWicyq2lXylCWyK0_BdO4"
TG_CHAT_ID = "5495608361" 

def send_tg_notification(code):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    text = f"🚀 *New Copy Detected!*\n\nCode: `{code}`\nSite: [sophiapromo.codes](https://sophiapromo.codes)"
    payload = {"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
    except:
        pass

# --- DATABASE HELPERS ---
def load_codes():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump([], f)
        return []
    with open(DATA_FILE, 'r') as f:
        try:
            return json.load(f)
        except:
            return []

def save_codes(codes):
    with open(DATA_FILE, 'w') as f:
        json.dump(codes, f, indent=4)

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('index.html', codes=load_codes())

@app.route('/track-copy', methods=['POST'])
def track_copy():
    data = request.get_json()
    code_val = data.get('code')
    codes = load_codes()
    for c in codes:
        if c['code'] == code_val:
            c['clicks'] = c.get('clicks', 0) + 1
            break
    save_codes(codes)
    send_tg_notification(code_val)
    return '', 204

@app.route('/manage-zemy-codes', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        user = request.form.get('username')
        pw = request.form.get('password')
        if user == ADMIN_USER and check_password_hash(ADMIN_PASSWORD_HASH, pw):
            session.permanent = True
            session['logged_in'] = True
            return redirect(url_for('admin'))
    
    if not session.get('logged_in'):
        return '''<body style="font-family:sans-serif; background:#f1f5f9; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;"><form method="post" style="background:white; padding:2rem; border-radius:1rem; box-shadow:0 10px 25px rgba(0,0,0,0.1);"><h2 style="text-align:center;">Login</h2><input name="username" placeholder="User" style="display:block; width:100%; margin-bottom:1rem; padding:0.5rem;"><input name="password" type="password" placeholder="Pass" style="display:block; width:100%; margin-bottom:1rem; padding:0.5rem;"><button style="width:100%; padding:0.5rem; background:#2563eb; color:white; border:none; border-radius:5px;">Login</button></form></body>'''
    
    return render_template('admin.html', codes=load_codes())

@app.route('/add', methods=['POST'])
def add_code():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    raw_input = request.form.get('bulk_codes', '')
    incoming = [c.strip() for c in raw_input.split('\n') if c.strip()]
    if incoming:
        data = load_codes()
        existing = [item['code'] for item in data]
        for c in incoming:
            if c not in existing:
                data.append({"id": int(time.time() * 1000), "code": c, "clicks": 0})
        save_codes(data)
    return redirect(url_for('admin'))

@app.route('/bulk-delete', methods=['POST'])
def bulk_delete():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    raw_input = request.form.get('delete_list', '')
    to_remove = [c.strip() for c in raw_input.split('\n') if c.strip()]
    if to_remove:
        current = load_codes()
        updated = [c for c in current if c['code'] not in to_remove]
        save_codes(updated)
    return redirect(url_for('admin'))

@app.route('/delete/<int:id>')
def delete_single(id):
    if not session.get('logged_in'): return redirect(url_for('admin'))
    save_codes([c for c in load_codes() if c['id'] != id])
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)        except:
            return []

def save_codes(codes):
    with open(DATA_FILE, 'w') as f:
        json.dump(codes, f, indent=4)

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('index.html', codes=load_codes())

@app.route('/track-copy', methods=['POST'])
def track_copy():
    data = request.get_json()
    code_val = data.get('code')
    codes = load_codes()
    for c in codes:
        if c['code'] == code_val:
            c['clicks'] = c.get('clicks', 0) + 1
            break
    save_codes(codes)
    send_tg_notification(code_val)
    return '', 204

@app.route('/manage-zemy-codes', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        user = request.form.get('username')
        pw = request.form.get('password')
        if user == ADMIN_USER and check_password_hash(ADMIN_PASSWORD_HASH, pw):
            session.permanent = True
            session['logged_in'] = True
            return redirect(url_for('admin'))
    
    if not session.get('logged_in'):
        return '''<body style="font-family:sans-serif; background:#f1f5f9; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;"><form method="post" style="background:white; padding:2rem; border-radius:1rem; box-shadow:0 10px 25px rgba(0,0,0,0.1);"><h2 style="text-align:center;">Login</h2><input name="username" placeholder="User" style="display:block; width:100%; margin-bottom:1rem; padding:0.5rem;"><input name="password" type="password" placeholder="Pass" style="display:block; width:100%; margin-bottom:1rem; padding:0.5rem;"><button style="width:100%; padding:0.5rem; background:#2563eb; color:white; border:none; border-radius:5px;">Login</button></form></body>'''
    
    return render_template('admin.html', codes=load_codes())

@app.route('/add', methods=['POST'])
def add_code():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    raw_input = request.form.get('bulk_codes', '')
    incoming = [c.strip() for c in raw_input.split('\n') if c.strip()]
    if incoming:
        data = load_codes()
        existing = [item['code'] for item in data]
        for c in incoming:
            if c not in existing:
                data.append({"id": int(time.time() * 1000), "code": c, "clicks": 0})
        save_codes(data)
    return redirect(url_for('admin'))

@app.route('/bulk-delete', methods=['POST'])
def bulk_delete():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    raw_input = request.form.get('delete_list', '')
    to_remove = [c.strip() for c in raw_input.split('\n') if c.strip()]
    if to_remove:
        current = load_codes()
        updated = [c for c in current if c['code'] not in to_remove]
        save_codes(updated)
    return redirect(url_for('admin'))

@app.route('/delete/<int:id>')
def delete_single(id):
    if not session.get('logged_in'): return redirect(url_for('admin'))
    save_codes([c for c in load_codes() if c['id'] != id])
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

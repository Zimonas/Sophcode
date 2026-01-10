import os, json, time
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "zemy_master_key_2026" 
app.permanent_session_lifetime = timedelta(days=7)

# --- CONFIGURATION ---
ADMIN_USER = "MasterZanix"
ADMIN_PASSWORD_HASH = "scrypt:32768:8:1$mCa1VowXKLSWJEYy$45b2f9e646b1b65bb75ab849227e86018d91bb30ad6bbeab513fe2a944c5876d4e25c2e23fdffc3478b560ab43ab81966ef0eeec755b9b9c87c8d51f25219448"
DATA_FILE = 'codes.json'

def load_codes():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f: json.dump([], f)
        return []
    with open(DATA_FILE, 'r') as f:
        try: return json.load(f)
        except: return []

def save_codes(codes):
    with open(DATA_FILE, 'w') as f: json.dump(codes, f, indent=4)

# --- PUBLIC ROUTE ---
@app.route('/')
def index():
    return render_template('index.html', codes=load_codes())

# --- ADMIN CORE ---
@app.route('/manage-zemy-codes', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        user = request.form.get('username')
        pw = request.form.get('password')
        if user == ADMIN_USER and check_password_hash(ADMIN_PASSWORD_HASH, pw):
            session.permanent = True
            session['logged_in'] = True
            return redirect(url_for('admin'))
        flash("Invalid Credentials")
    
    if not session.get('logged_in'):
        return '''
        <body style="font-family:sans-serif; background:#f1f5f9; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;">
            <form method="post" style="background:white; padding:2.5rem; border-radius:1rem; box-shadow:0 10px 25px rgba(0,0,0,0.1); width:320px;">
                <h2 style="text-align:center; margin-top:0;">Zemy Admin</h2>
                <input name="username" placeholder="Username" required style="display:block; width:100%; margin-bottom:1rem; padding:0.8rem; border:1px solid #cbd5e1; border-radius:0.5rem; box-sizing:border-box;">
                <input name="password" type="password" placeholder="Password" required style="display:block; width:100%; margin-bottom:1.5rem; padding:0.8rem; border:1px solid #cbd5e1; border-radius:0.5rem; box-sizing:border-box;">
                <button style="width:100%; padding:0.8rem; background:#2563eb; color:white; border:none; border-radius:0.5rem; font-weight:bold; cursor:pointer;">Login</button>
            </form>
        </body>
        '''
    return render_template('admin.html', codes=load_codes())

# --- BULK OPERATIONS ---
@app.route('/add', methods=['POST'])
def add_code():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    raw_input = request.form.get('bulk_codes', '')
    incoming = [c.strip() for c in raw_input.split('\n') if c.strip()]
    if incoming:
        data = load_codes()
        existing = [item['code'] for item in data]
        added = 0
        for c in incoming:
            if c not in existing:
                data.append({"id": int(time.time() * 1000) + added, "code": c})
                existing.append(c)
                added += 1
        save_codes(data)
        flash(f"Added {added} new codes.")
    return redirect(url_for('admin'))

@app.route('/bulk-delete', methods=['POST'])
def bulk_delete():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    raw_input = request.form.get('delete_list', '')
    to_remove = [c.strip() for c in raw_input.split('\n') if c.strip()]
    if to_remove:
        current = load_codes()
        updated = [c for c in current if c['code'] not in to_remove]
        removed = len(current) - len(updated)
        save_codes(updated)
        flash(f"Removed {removed} codes from the list.")
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

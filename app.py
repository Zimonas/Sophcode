import os, json, time
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "zemy_final_secure_2026" 
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

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('index.html', codes=load_codes())

@app.route('/manage-zemy-codes', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form.get('username') == ADMIN_USER and \
           check_password_hash(ADMIN_PASSWORD_HASH, request.form.get('password')):
            session.permanent = True
            session['logged_in'] = True
            return redirect(url_for('admin'))
        flash("Invalid login credentials")
    
    if not session.get('logged_in'):
        return '''
        <body style="font-family:sans-serif; background:#f1f5f9; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;">
            <form method="post" style="background:white; padding:2rem; border-radius:1rem; box-shadow:0 10px 25px rgba(0,0,0,0.1); width:300px;">
                <h2 style="margin-bottom:1.5rem; text-align:center;">Zemy Admin</h2>
                <input name="username" placeholder="Username" style="display:block; width:100%; margin-bottom:1rem; padding:0.75rem; border:1px solid #ddd; border-radius:8px; box-sizing:border-box;">
                <input name="password" type="password" placeholder="Password" style="display:block; width:100%; margin-bottom:1.5rem; padding:0.75rem; border:1px solid #ddd; border-radius:8px; box-sizing:border-box;">
                <button style="width:100%; padding:0.75rem; background:#2563eb; color:white; border:none; border-radius:8px; font-weight:bold; cursor:pointer;">Login</button>
            </form>
        </body>
        '''
    return render_template('admin.html', codes=load_codes())

@app.route('/add', methods=['POST'])
def add_code():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    
    raw_input = request.form.get('bulk_codes', '')
    incoming_codes = [c.strip() for c in raw_input.split('\n') if c.strip()]
    
    if incoming_codes:
        existing_data = load_codes()
        existing_strings = [item['code'] for item in existing_data]
        
        added_count = 0
        for c in incoming_codes:
            # Duplicate Check logic
            if c not in existing_strings:
                existing_data.append({
                    "id": int(time.time() * 1000) + added_count,
                    "code": c
                })
                existing_strings.append(c)
                added_count += 1
        
        save_codes(existing_data)
        flash(f"Successfully added {added_count} unique codes!")
    return redirect(url_for('admin'))

@app.route('/delete/<int:id>')
def delete_code(id):
    if not session.get('logged_in'): return redirect(url_for('admin'))
    save_codes([c for c in load_codes() if c['id'] != id])
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)    if not session.get('logged_in'):
        return '''<body style="font-family:sans-serif; background:#f1f5f9; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;"><form method="post" style="background:white; padding:2rem; border-radius:1rem; box-shadow:0 10px 25px rgba(0,0,0,0.1);"><h2 style="margin-bottom:1rem">Zemy Login</h2><input name="username" placeholder="User" style="display:block; width:100%; margin-bottom:1rem; padding:0.5rem;"><input name="password" type="password" placeholder="Pass" style="display:block; width:100%; margin-bottom:1rem; padding:0.5rem;"><button style="width:100%; padding:0.5rem; background:#3b82f6; color:white; border:none; border-radius:5px;">Login</button></form></body>'''
    return render_template('admin.html', codes=load_codes())

@app.route('/add', methods=['POST'])
def add_code():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    
    # Bulk logic: Split the input by lines and remove empty spaces
    raw_input = request.form.get('bulk_codes', '')
    new_entries = [c.strip() for c in raw_input.split('\n') if c.strip()]
    
    if new_entries:
        codes = load_codes()
        for c in new_entries:
            codes.append({
                "id": int(time.time() * 1000) + new_entries.index(c), # Unique ID for each
                "code": c
            })
        save_codes(codes)
    return redirect(url_for('admin'))

@app.route('/delete/<int:id>')
def delete_code(id):
    if not session.get('logged_in'): return redirect(url_for('admin'))
    save_codes([c for c in load_codes() if c['id'] != id])
    return redirect(url_for('admin'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

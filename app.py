import os, json, time
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from datetime import timedelta

app = Flask(__name__)
# Stable secret key for sessions
app.secret_key = "zemy_stable_key_2026_v1" 
app.permanent_session_lifetime = timedelta(days=7)

# --- CONFIGURATION ---
ADMIN_USER = "MasterZanix"
# Combined into one solid line to prevent "Invalid Credentials" errors
ADMIN_PASSWORD_HASH = "scrypt:32768:8:1$mCa1VowXKLSWJEYy$45b2f9e646b1b65bb75ab849227e86018d91bb30ad6bbeab513fe2a944c5876d4e25c2e23fdffc3478b560ab43ab81966ef0eeec755b9b9c87c8d51f25219448"
DATA_FILE = 'codes.json'

def load_codes():
    if not os.path.exists(DATA_FILE):
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

@app.route('/manage-zemy-codes', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        user = request.form.get('username')
        pw = request.form.get('password')
        
        if user == ADMIN_USER and check_password_hash(ADMIN_PASSWORD_HASH, pw):
            session.permanent = True
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            flash("Invalid Credentials")
            return redirect(url_for('admin'))
    
    if not session.get('logged_in'):
        return '''
        <body style="font-family:sans-serif; background:#f0f2f5; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;">
            <form method="post" style="background:white; padding:2rem; border-radius:1rem; box-shadow:0 10px 25px rgba(0,0,0,0.1); width:300px;">
                <h2 style="margin:0 0 1.5rem 0; color:#1e293b; text-align:center;">Zemy Admin</h2>
                <input name="username" placeholder="Username" style="display:block; width:100%; margin-bottom:1rem; padding:0.75rem; border:1px solid #ddd; border-radius:8px; box-sizing:border-box;">
                <input name="password" type="password" placeholder="Password" style="display:block; width:100%; margin-bottom:1.5rem; padding:0.75rem; border:1px solid #ddd; border-radius:8px; box-sizing:border-box;">
                <button style="width:100%; padding:0.75rem; background:#2563eb; color:white; border:none; border-radius:8px; font-weight:bold; cursor:pointer;">Login</button>
                <p style="text-align:center; color:red; font-size:0.8rem;">''' + (flash_msg if (flash_msg := "".join(list(session.get('_flashes', {}).values()) if '_flashes' in session else [])) else "") + '''</p>
            </form>
        </body>
        '''
    
    return render_template('admin.html', codes=load_codes())

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/add', methods=['POST'])
def add_code():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    codes = load_codes()
    codes.append({"id": int(time.time()), "name": request.form['name'], "code": request.form['code']})
    save_codes(codes)
    return redirect(url_for('admin'))

@app.route('/delete/<int:id>')
def delete_code(id):
    if not session.get('logged_in'): return redirect(url_for('admin'))
    codes = [c for c in load_codes() if c['id'] != id]
    save_codes(codes)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

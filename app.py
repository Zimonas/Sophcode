import os, json, time
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from datetime import timedelta

app = Flask(__name__)
# IMPORTANT: Use a fixed string, NOT os.urandom, so Heroku doesn't log you out on restart
app.secret_key = "ZemyTools_Secure_2026_Key_Keep_Fixed" 
app.permanent_session_lifetime = timedelta(days=7) # Stay logged in for a week

ADMIN_USER = "MasterZanix"
# Use the hash for 'Simonasx18@2005'
ADMIN_PASSWORD_HASH = "scrypt:32768:8:1$C8j9m1PqR3xT5vWz$f8e912c345a67890b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4"
DATA_FILE = 'codes.json'

# --- HELPERS ---
def load_codes():
    if not os.path.exists(DATA_FILE): return []
    try:
        with open(DATA_FILE, 'r') as f: return json.load(f)
    except: return []

def save_codes(codes):
    with open(DATA_FILE, 'w') as f: json.dump(codes, f, indent=4)

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('index.html', codes=load_codes())

# SECRET ADMIN ROUTE (Users won't find this)
@app.route('/zemy-dashboard-control', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form.get('username') == ADMIN_USER and \
           check_password_hash(ADMIN_PASSWORD_HASH, request.form.get('password')):
            session.permanent = True
            session['logged_in'] = True
            return redirect(url_for('admin'))
        flash("Invalid login")
    
    if not session.get('logged_in'):
        return render_template('login.html') # Create a simple login.html or use the inline one
    
    return render_template('admin.html', codes=load_codes())

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- HIDE FROM GOOGLE ---
@app.route('/robots.txt')
def robots():
    return "User-agent: *\nDisallow: /zemy-dashboard-control"

# --- OPERATIONS ---
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
    app.run(debug=True)        if username == ADMIN_USER and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            flash("Invalid Credentials")
    
    if not session.get('logged_in'):
        # Modern login form if not logged in
        return '''
        <body style="font-family:sans-serif; background:#f0f2f5; display:flex; justify-content:center; align-items:center; height:100vh;">
            <form method="post" style="background:white; padding:2rem; border-radius:1rem; shadow:0 4px 6px -1px rgba(0,0,0,0.1);">
                <h2 style="margin-top:0">Admin Login</h2>
                <input name="username" placeholder="Username" style="display:block; width:100%; margin-bottom:1rem; padding:0.5rem; border:1px solid #ccc; border-radius:5px;">
                <input name="password" type="password" placeholder="Password" style="display:block; width:100%; margin-bottom:1rem; padding:0.5rem; border:1px solid #ccc; border-radius:5px;">
                <button style="width:100%; padding:0.75rem; background:#2563eb; color:white; border:none; border-radius:5px; cursor:pointer;">Login</button>
            </form>
        </body>
        '''
    
    return render_template('admin.html', codes=load_codes())

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin'))

@app.route('/add', methods=['POST'])
def add_code():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    codes = load_codes()
    # Create a unique ID based on timestamp to avoid conflicts
    import time
    new_id = int(time.time())
    codes.append({"id": new_id, "name": request.form['name'], "code": request.form['code']})
    save_codes(codes)
    return redirect(url_for('admin'))

@app.route('/delete/<int:id>')
def delete_code(id):
    if not session.get('logged_in'): return redirect(url_for('admin'))
    codes = [c for c in load_codes() if c['id'] != id]
    save_codes(codes)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)

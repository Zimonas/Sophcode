import os, json, time
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from datetime import timedelta

app = Flask(__name__)

# --- STABLE CONFIGURATION ---
# This ensures you stay logged in even if the server restarts
app.secret_key = "zemy_stable_secure_key_2026_v2" 
app.permanent_session_lifetime = timedelta(days=7)

# Your Credentials
ADMIN_USER = "MasterZanix"
# Your exact hash for "Simonasx18@2005" on a single line
ADMIN_PASSWORD_HASH = "scrypt:32768:8:1$mCa1VowXKLSWJEYy$45b2f9e646b1b65bb75ab849227e86018d91bb30ad6bbeab513fe2a944c5876d4e25c2e23fdffc3478b560ab43ab81966ef0eeec755b9b9c87c8d51f25219448"

DATA_FILE = 'codes.json'

# --- DATABASE HELPERS ---
def load_codes():
    if not os.path.exists(DATA_FILE):
        # Create empty file if it doesn't exist
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

# --- PUBLIC ROUTES ---
@app.route('/')
def index():
    return render_template('index.html', codes=load_codes())

# --- SECRET ADMIN DASHBOARD ---
@app.route('/manage-zemy-codes', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        user = request.form.get('username')
        pw = request.form.get('password')
        
        # Compare typed password against the hash
        if user == ADMIN_USER and check_password_hash(ADMIN_PASSWORD_HASH, pw):
            session.permanent = True
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            flash("Invalid Credentials")
            return redirect(url_for('admin'))
    
    # If not logged in, show the simple login form
    if not session.get('logged_in'):
        return '''
        <body style="font-family:sans-serif; background:#f1f5f9; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;">
            <form method="post" style="background:white; padding:2.5rem; border-radius:1rem; box-shadow:0 20px 25px -5px rgba(0,0,0,0.1); width:320px;">
                <h2 style="margin:0 0 1.5rem 0; color:#0f172a; text-align:center;">Zemy Dashboard</h2>
                <input name="username" placeholder="Username" required style="display:block; width:100%; margin-bottom:1rem; padding:0.8rem; border:1px solid #cbd5e1; border-radius:0.5rem; box-sizing:border-box;">
                <input name="password" type="password" placeholder="Password" required style="display:block; width:100%; margin-bottom:1.5rem; padding:0.8rem; border:1px solid #cbd5e1; border-radius:0.5rem; box-sizing:border-box;">
                <button style="width:100%; padding:0.8rem; background:#3b82f6; color:white; border:none; border-radius:0.5rem; font-weight:bold; cursor:pointer;">Sign In</button>
            </form>
        </body>
        '''
    
    return render_template('admin.html', codes=load_codes())

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- CODE OPERATIONS ---
@app.route('/add', methods=['POST'])
def add_code():
    if not session.get('logged_in'): 
        return redirect(url_for('admin'))
    
    name = request.form.get('name')
    code_val = request.form.get('code')
    
    if name and code_val:
        codes = load_codes()
        # Use timestamp as a unique ID for easy deleting
        codes.append({
            "id": int(time.time()), 
            "name": name, 
            "code": code_val
        })
        save_codes(codes)
        
    return redirect(url_for('admin'))

@app.route('/delete/<int:id>')
def delete_code(id):
    if not session.get('logged_in'): 
        return redirect(url_for('admin'))
    
    codes = load_codes()
    # Filter out the code with the matching ID
    new_codes = [c for c in codes if c['id'] != id]
    save_codes(new_codes)
    
    return redirect(url_for('admin'))

# --- ERROR HANDLING ---
@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404 - Page Not Found</h1><p>The page you are looking for doesn't exist.</p>", 404

# --- RUN APP ---
if __name__ == '__main__':
    # Heroku provides a PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

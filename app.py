import os, json, time
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from datetime import timedelta

app = Flask(__name__)
# Stable secret key so you don't get logged out
app.secret_key = "zemy_stable_key_123" 
app.permanent_session_lifetime = timedelta(days=7)

ADMIN_USER = "MasterZanix"
# This is the FIXED hash for Simonasx18@2005
ADMIN_PASSWORD_HASH = "scrypt:32768:8:1$C8j9m1PqR3xT5vWz$f8e912c345a67890b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4"

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

@app.route('/')
def index():
    return render_template('index.html', codes=load_codes())

# Changed to a secret URL so people can't find your login easily
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
            return "Invalid Credentials. <a href='/manage-zemy-codes'>Try again</a>"
    
    if not session.get('logged_in'):
        return '''
        <form method="post" style="margin-top:50px; text-align:center;">
            <h2>Zemy Admin Login</h2>
            <input name="username" placeholder="Username"><br><br>
            <input name="password" type="password" placeholder="Password"><br><br>
            <button type="submit">Login</button>
        </form>
        '''
    
    return render_template('admin.html', codes=load_codes())

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

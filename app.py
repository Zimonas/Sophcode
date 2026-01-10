import os, json
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "CJSBSIIH9299181BXKQBSIDNSKXJXXCTRLQNDGVCOMDN" # Required for sessions

# --- CONFIGURATION ---
ADMIN_USER = "MasterZanix"
# RUN THIS ONCE TO GENERATE A HASH: generate_password_hash("SimGir247@")
# Replace the string below with your generated hash
ADMIN_PASSWORD_HASH = generate_password_hash("SimGir247@") 
DATA_FILE = 'codes.json'

def load_codes():
    if not os.path.exists(DATA_FILE): return []
    with open(DATA_FILE, 'r') as f: return json.load(f)

def save_codes(codes):
    with open(DATA_FILE, 'w') as f: json.dump(codes, f, indent=4)

@app.route('/')
def index():
    return render_template('index.html', codes=load_codes())

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form.get('username') == ADMIN_USER and \
           check_password_hash(ADMIN_PASSWORD_HASH, request.form.get('password')):
            session['logged_in'] = True
            return redirect(url_for('admin'))
        flash("Invalid Credentials")
    
    if not session.get('logged_in'):
        return '''<form method="post">User: <input name="username"><br>Pass: <input type="password" name="password"><button>Login</button></form>'''
    
    return render_template('admin.html', codes=load_codes())

@app.route('/add', methods=['POST'])
def add_code():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    codes = load_codes()
    codes.append({"id": len(codes), "name": request.form['name'], "code": request.form['code']})
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

import os, json, time, requests
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash
from datetime import timedelta

app = Flask(__name__)

# --- CONFIG ---
app.secret_key = os.environ.get("SECRET_KEY", "dev_fallback")
app.permanent_session_lifetime = timedelta(days=7)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax"
)

ADMIN_USER = os.environ.get("ADMIN_USER", "MasterZanix")
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH")

DATA_FILE = "codes.json"

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

# --- HELPERS ---
def load_codes():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)
    try:
        with open(DATA_FILE) as f:
            return json.load(f)
    except:
        return []

def save_codes(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def send_tg(code):
    if not TG_TOKEN or not TG_CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={
                "chat_id": TG_CHAT_ID,
                "text": f"🚀 *New Copy Detected!*\n\nCode: `{code}`",
                "parse_mode": "Markdown"
            },
            timeout=5
        )
    except:
        pass

# --- ROUTES ---
@app.route("/")
def index():
    return render_template("index.html", codes=load_codes())

@app.route("/track-copy", methods=["POST"])
def track_copy():
    data = request.get_json(silent=True) or {}
    code = data.get("code")
    if not code:
        return "", 400

    codes = load_codes()
    for c in codes:
        if c["code"] == code:
            c["clicks"] = c.get("clicks", 0) + 1
            save_codes(codes)
            send_tg(code)
            break
    return "", 204

@app.route("/manage-zemy-codes", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if (
            request.form.get("username") == ADMIN_USER
            and ADMIN_PASSWORD_HASH
            and check_password_hash(
                ADMIN_PASSWORD_HASH, request.form.get("password")
            )
        ):
            session["logged_in"] = True
            session.permanent = True
            return redirect(url_for("admin"))

    if not session.get("logged_in"):
        return render_template("login.html") if False else """
        <form method="post" style="max-width:300px;margin:100px auto">
        <h2>Admin Login</h2>
        <input name="username" placeholder="Username"><br><br>
        <input type="password" name="password" placeholder="Password"><br><br>
        <button>Login</button>
        </form>
        """

    return render_template("admin.html", codes=load_codes())

@app.route("/add", methods=["POST"])
def add():
    if not session.get("logged_in"):
        return redirect(url_for("admin"))

    raw = request.form.get("bulk_codes", "")
    incoming = [c.strip() for c in raw.splitlines() if c.strip()]

    data = load_codes()
    existing = {c["code"] for c in data}

    for c in incoming:
        if c not in existing:
            data.append({
                "id": int(time.time() * 1000),
                "code": c,
                "clicks": 0
            })

    save_codes(data)
    return redirect(url_for("admin"))

@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    if not session.get("logged_in"):
        return redirect(url_for("admin"))
    save_codes([c for c in load_codes() if c["id"] != id])
    return redirect(url_for("admin"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

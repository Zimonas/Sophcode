< script >
  let copyCooldown = 0;
const container = document.getElementById('codes-container');
const toast = document.getElementById('toast');

// Live polling every 2s
async function pollCodes() {
  try {
    const res = await fetch('/api/codes');
    const codes = await res.json();
    // Update DOM with new counts (preserve animations)
    codes.forEach(c => {
      const item = container.querySelector(`[data-code="${c.code}"]`);
      if (item && parseInt(item.dataset.clicks) !== c.clicks) {
        item.dataset.clicks = c.clicks;
        item.classList.add('updating');
        const clicksEl = item.querySelector('.clicks');
        clicksEl.textContent = `${c.clicks} ${c.clicks === 1 ? 'copy' : 'copies'}`;
        setTimeout(() => item.classList.remove('updating'), 600);
      }
    });
  } catch (e) {}
  setTimeout(pollCodes, 2000);
}
pollCodes();

// Copy handler (unchanged)
document.addEventListener('copy', (e) => {
  const now = Date.now();
  if (now - copyCooldown < 1000) return;
  copyCooldown = now;
  const code = window.getSelection()?.toString().trim();
  if (!code || !/^[a-zA-Z0-9]{6,20}$/.test(code)) return;
  fetch('/track-copy', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code })
  }).then(() => {
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2000);
  });
}); <
/script>                cur.execute('CREATE TABLE IF NOT EXISTS codes (id SERIAL PRIMARY KEY, code TEXT UNIQUE NOT NULL, clicks INTEGER DEFAULT 0)')
            con.commit()
    except Exception as e:
        print(f"DB Init Error: {e}")

init_db()

# --- TELEGRAM ---
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

# --- LIVE UPDATES ---
@app.route('/live-updates')
def live_updates():
    def event_stream():
        known_counts = {}
        while True:
            try:
                with get_db() as con:
                    with con.cursor() as cur:
                        cur.execute("SELECT code, clicks FROM codes")
                        rows = cur.fetchall()
                        
                        for row in rows:
                            code = row['code']
                            clicks = row['clicks']
                            if known_counts.get(code) != clicks:
                                yield f"data: {json.dumps({'code': code, 'clicks': clicks})}\n\n"
                                known_counts[code] = clicks
                time.sleep(2)
            except GeneratorExit:
                break
            except:
                time.sleep(5)
    return Response(event_stream(), mimetype="text/event-stream")

# --- ROUTES ---
@app.route("/")
def index():
    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("SELECT id, code, clicks FROM codes ORDER BY id DESC")
            codes = cur.fetchall()
    return render_template("index.html", codes=codes)

@app.route("/track-copy", methods=["POST"])
def track_copy():
    data = request.get_json(silent=True) or {}
    code = data.get("code")
    if not code:
        return "", 400

    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("UPDATE codes SET clicks = clicks + 1 WHERE code = %s", (code,))
            con.commit()
            if cur.rowcount:
                send_tg(code)
    return "", 204

@app.route("/manage-zemy-codes", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if (
            request.form.get("username") == ADMIN_USER
            and ADMIN_PASSWORD_HASH
            and check_password_hash(ADMIN_PASSWORD_HASH, request.form.get("password"))
        ):
            session["logged_in"] = True
            session.permanent = True
            return redirect(url_for("admin"))

    if not session.get("logged_in"):
        return render_template("login.html")

    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("SELECT id, code, clicks FROM codes ORDER BY id DESC")
            codes = cur.fetchall()
    return render_template("admin.html", codes=codes)

@app.route("/add", methods=["POST"])
def add():
    if not session.get("logged_in"):
        return redirect(url_for("admin"))

    raw = request.form.get("bulk_codes", "")
    incoming = [c.strip() for c in raw.splitlines() if c.strip()]

    with get_db() as con:
        with con.cursor() as cur:
            for c in incoming:
                cur.execute("INSERT INTO codes (code) VALUES (%s) ON CONFLICT DO NOTHING", (c,))
        con.commit()
    return redirect(url_for("admin"))

@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    if not session.get("logged_in"):
        return redirect(url_for("admin"))

    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("DELETE FROM codes WHERE id = %s", (id,))
        con.commit()
    return redirect(url_for("admin"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
                cur.execute('CREATE TABLE IF NOT EXISTS codes (id SERIAL PRIMARY KEY, code TEXT UNIQUE NOT NULL, clicks INTEGER DEFAULT 0)')
            con.commit()
    except Exception as e:
        print(f"DB Init Error: {e}")

init_db()

# --- TELEGRAM ---
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

# --- LIVE UPDATES (SIMPLEST VERSION) ---
@app.route('/live-updates')
def live_updates():
    def event_stream():
        known_counts = {}
        while True:
            try:
                with get_db() as con:
                    with con.cursor() as cur:
                        cur.execute("SELECT code, clicks FROM codes")
                        rows = cur.fetchall()
                        
                        for row in rows:
                            code = row['code']
                            clicks = row['clicks']
                            if known_counts.get(code) != clicks:
                                yield f"data: {json.dumps({'code': code, 'clicks': clicks})}\n\n"
                                known_counts[code] = clicks
                time.sleep(2)
            except GeneratorExit:
                break
            except:
                time.sleep(5)
    return Response(event_stream(), mimetype="text/event-stream")

# --- ROUTES ---
@app.route("/")
def index():
    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("SELECT id, code, clicks FROM codes ORDER BY id DESC")
            codes = cur.fetchall()
    return render_template("index.html", codes=codes)

@app.route("/track-copy", methods=["POST"])
def track_copy():
    data = request.get_json(silent=True) or {}
    code = data.get("code")
    if not code:
        return "", 400

    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("UPDATE codes SET clicks = clicks + 1 WHERE code = %s", (code,))
            con.commit()
            if cur.rowcount:
                send_tg(code)
    return "", 204

@app.route("/manage-zemy-codes", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if (
            request.form.get("username") == ADMIN_USER
            and ADMIN_PASSWORD_HASH
            and check_password_hash(ADMIN_PASSWORD_HASH, request.form.get("password"))
        ):
            session["logged_in"] = True
            session.permanent = True
            return redirect(url_for("admin"))

    if not session.get("logged_in"):
        return render_template("login.html")

    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("SELECT id, code, clicks FROM codes ORDER BY id DESC")
            codes = cur.fetchall()
    return render_template("admin.html", codes=codes)

@app.route("/add", methods=["POST"])
def add():
    if not session.get("logged_in"):
        return redirect(url_for("admin"))

    raw = request.form.get("bulk_codes", "")
    incoming = [c.strip() for c in raw.splitlines() if c.strip()]

    with get_db() as con:
        with con.cursor() as cur:
            for c in incoming:
                cur.execute("INSERT INTO codes (code) VALUES (%s) ON CONFLICT DO NOTHING", (c,))
        con.commit()
    return redirect(url_for("admin"))

@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    if not session.get("logged_in"):
        return redirect(url_for("admin"))

    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("DELETE FROM codes WHERE id = %s", (id,))
        con.commit()
    return redirect(url_for("admin"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS codes (
                        id SERIAL PRIMARY KEY,
                        code TEXT UNIQUE NOT NULL,
                        clicks INTEGER DEFAULT 0
                    )
                """)
            con.commit()
    except Exception as e:
        print(f"DB Init Error: {e}")

init_db()

# --- TELEGRAM ---
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

# --- LIVE UPDATES ---
@app.route('/live-updates')
def live_updates():
    def event_stream():
        known_counts = {}
        while True:
            try:
                with get_db() as con:
                    with con.cursor() as cur:
                        cur.execute("SELECT code, clicks FROM codes")
                        rows = cur.fetchall()
                        
                        for row in rows:
                            c_code = row['code']
                            c_clicks = row['clicks']
                            
                            if known_counts.get(c_code) != c_clicks:
                                data = json.dumps({"code": c_code, "clicks": c_clicks})
                                yield f"data: {data}\n\n"
                                known_counts[c_code] = c_clicks
                                
                time.sleep(2)
            except GeneratorExit:
                break
            except Exception as e:
                print(f"Stream Error: {e}")
                time.sleep(5)

    return Response(event_stream(), mimetype="text/event-stream")

# --- ROUTES ---
@app.route("/")
def index():
    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("SELECT id, code, clicks FROM codes ORDER BY id DESC")
            codes = cur.fetchall()
    return render_template("index.html", codes=codes)

@app.route("/track-copy", methods=["POST"])
def track_copy():
    data = request.get_json(silent=True) or {}
    code = data.get("code")
    if not code:
        return "", 400

    with get_db() as con:
        with con.cursor() as cur:
            cur.execute(
                "UPDATE codes SET clicks = clicks + 1 WHERE code = %s",
                (code,)
            )
            con.commit()  # CRITICAL: Save immediately for live updates
            if cur.rowcount:
                send_tg(code)

    return "", 204

@app.route("/manage-zemy-codes", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if (
            request.form.get("username") == ADMIN_USER
            and ADMIN_PASSWORD_HASH
            and check_password_hash(
                ADMIN_PASSWORD_HASH,
                request.form.get("password")
            )
        ):
            session["logged_in"] = True
            session.permanent = True
            return redirect(url_for("admin"))

    if not session.get("logged_in"):
        return render_template("login.html")

    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("SELECT id, code, clicks FROM codes ORDER BY id DESC")
            codes = cur.fetchall()

    return render_template("admin.html", codes=codes)

@app.route("/add", methods=["POST"])
def add():
    if not session.get("logged_in"):
        return redirect(url_for("admin"))

    raw = request.form.get("bulk_codes", "")
    incoming = [c.strip() for c in raw.splitlines() if c.strip()]

    with get_db() as con:
        with con.cursor() as cur:
            for c in incoming:
                cur.execute(
                    "INSERT INTO codes (code) VALUES (%s) ON CONFLICT DO NOTHING",
                    (c,)
                )
        con.commit()

    return redirect(url_for("admin"))

@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    if not session.get("logged_in"):
        return redirect(url_for("admin"))

    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("DELETE FROM codes WHERE id = %s", (id,))
        con.commit()

    return redirect(url_for("admin"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# --- RUN ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS codes (
                        id SERIAL PRIMARY KEY,
                        code TEXT UNIQUE NOT NULL,
                        clicks INTEGER DEFAULT 0
                    )
                """)
            con.commit()
    except Exception as e:
        print(f"DB Init Error: {e}")

init_db()

# --- TELEGRAM ---
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
    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("SELECT id, code, clicks FROM codes ORDER BY id DESC")
            codes = cur.fetchall()
    return render_template("index.html", codes=codes)

@app.route('/live-updates')
def live_updates():
    def event_stream():
        # Cache to track changes and avoid sending duplicate data
        known_counts = {}
        while True:
            try:
                with get_db() as con:
                    with con.cursor() as cur:
                        cur.execute("SELECT code, clicks FROM codes")
                        rows = cur.fetchall()
                        
                        for row in rows:
                            c_code = row['code']
                            c_clicks = row['clicks']
                            
                            # Only send update if count changed or it's new
                            if known_counts.get(c_code) != c_clicks:
                                data = json.dumps({"code": c_code, "clicks": c_clicks})
                                yield f"data: {data}\n\n"
                                known_counts[c_code] = c_clicks
                                
                time.sleep(2)  # Check for updates every 2 seconds
            except Exception as e:
                print(f"Stream Error: {e}")
                time.sleep(5) # Wait longer on error before retrying

    return Response(event_stream(), mimetype="text/event-stream")

@app.route("/track-copy", methods=["POST"])
def track_copy():
    data = request.get_json(silent=True) or {}
    code = data.get("code")
    if not code:
        return "", 400

    with get_db() as con:
        with con.cursor() as cur:
            cur.execute(
                "UPDATE codes SET clicks = clicks + 1 WHERE code = %s",
                (code,)
            )
            con.commit()  # IMPORTANT: Save the change immediately
            if cur.rowcount:
                send_tg(code)

    return "", 204

@app.route("/manage-zemy-codes", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if (
            request.form.get("username") == ADMIN_USER
            and ADMIN_PASSWORD_HASH
            and check_password_hash(
                ADMIN_PASSWORD_HASH,
                request.form.get("password")
            )
        ):
            session["logged_in"] = True
            session.permanent = True
            return redirect(url_for("admin"))

    if not session.get("logged_in"):
        return render_template("login.html")

    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("SELECT id, code, clicks FROM codes ORDER BY id DESC")
            codes = cur.fetchall()

    return render_template("admin.html", codes=codes)

@app.route("/add", methods=["POST"])
def add():
    if not session.get("logged_in"):
        return redirect(url_for("admin"))

    raw = request.form.get("bulk_codes", "")
    incoming = [c.strip() for c in raw.splitlines() if c.strip()]

    with get_db() as con:
        with con.cursor() as cur:
            for c in incoming:
                cur.execute(
                    "INSERT INTO codes (code) VALUES (%s) ON CONFLICT DO NOTHING",
                    (c,)
                )
        con.commit()

    return redirect(url_for("admin"))

@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    if not session.get("logged_in"):
        return redirect(url_for("admin"))

    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("DELETE FROM codes WHERE id = %s", (id,))
        con.commit()

    return redirect(url_for("admin"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# --- RUN ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
                    id SERIAL PRIMARY KEY,
                    code TEXT UNIQUE NOT NULL,
                    clicks INTEGER DEFAULT 0
                )
            """)

init_db()

# --- TELEGRAM ---
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

# --- LIVE UPDATES (SSE) ---
last_event_id = 0

@app.route('/live-updates')
def live_updates():
    def event_stream():
        nonlocal last_event_id
        last_id = request.args.get('last_id', last_event_id, type=int)
        
        while True:
            with get_db() as con:
                with con.cursor() as cur:
                    cur.execute("""
                        SELECT id, code, clicks 
                        FROM codes 
                        WHERE id > %s AND clicks > COALESCE((SELECT clicks FROM codes WHERE code = codes.code AND id <= %s), 0)
                        ORDER BY id ASC LIMIT 1
                    """, (last_id, last_id))
                    row = cur.fetchone()
                    
                    if row:
                        yield f"data: {json.dumps({'code': row['code'], 'clicks': row['clicks']})}\n\n"
                        last_event_id = row['id']
                        last_id = row['id']
                    else:
                        yield ": heartbeat\n\n"
            
            import time
            time.sleep(1)
    
    return Response(event_stream(), mimetype="text/event-stream")

# --- ROUTES ---
@app.route("/")
def index():
    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("SELECT id, code, clicks FROM codes ORDER BY id DESC")
            codes = cur.fetchall()
    return render_template("index.html", codes=codes)

@app.route("/track-copy", methods=["POST"])
def track_copy():
    data = request.get_json(silent=True) or {}
    code = data.get("code")
    if not code:
        return "", 400

    with get_db() as con:
        with con.cursor() as cur:
            cur.execute(
                "UPDATE codes SET clicks = clicks + 1 WHERE code = %s RETURNING id, code, clicks",
                (code,)
            )
            row = cur.fetchone()
            if row:
                send_tg(code)

    return "", 204

@app.route("/manage-zemy-codes", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if (
            request.form.get("username") == ADMIN_USER
            and ADMIN_PASSWORD_HASH
            and check_password_hash(
                ADMIN_PASSWORD_HASH,
                request.form.get("password")
            )
        ):
            session["logged_in"] = True
            session.permanent = True
            return redirect(url_for("admin"))

    if not session.get("logged_in"):
        return render_template("login.html")

    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("SELECT id, code, clicks FROM codes ORDER BY id DESC")
            codes = cur.fetchall()

    return render_template("admin.html", codes=codes)

@app.route("/add", methods=["POST"])
def add():
    if not session.get("logged_in"):
        return redirect(url_for("admin"))

    raw = request.form.get("bulk_codes", "")
    incoming = [c.strip() for c in raw.splitlines() if c.strip()]

    with get_db() as con:
        with con.cursor() as cur:
            for c in incoming:
                cur.execute(
                    "INSERT INTO codes (code) VALUES (%s) ON CONFLICT DO NOTHING",
                    (c,)
                )
        con.commit()

    return redirect(url_for("admin"))

@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    if not session.get("logged_in"):
        return redirect(url_for("admin"))

    with get_db() as con:
        with con.cursor() as cur:
            cur.execute("DELETE FROM codes WHERE id = %s", (id,))
        con.commit()

    return redirect(url_for("admin"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# --- RUN ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

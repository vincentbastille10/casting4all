from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
DB = "castings.db"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ==============================
# DATABASE INIT
# ==============================
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS castings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        platform TEXT,
        city TEXT,
        description_public TEXT,
        description_private TEXT,
        image TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ==============================
# ROUTES HTML
# ==============================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# ==============================
# SERVE IMAGES
# ==============================
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ==============================
# GET CASTINGS
# ==============================
@app.route("/api/castings", methods=["GET"])
def get_castings():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT * FROM castings ORDER BY id DESC")
    rows = c.fetchall()

    conn.close()

    castings = []
    for row in rows:
        castings.append({
            "id": row[0],
            "title": row[1],
            "platform": row[2],
            "city": row[3],
            "description_public": row[4],
            "description_private": row[5],
            "image": f"/uploads/{row[6]}",
            "created_at": row[7],
            "locked": True  # important pour ta landing
        })

    return jsonify(castings)

# ==============================
# ADD CASTING
# ==============================
@app.route("/api/castings", methods=["POST"])
def add_casting():
    title = request.form.get("title")
    platform = request.form.get("platform")
    city = request.form.get("city")
    description_public = request.form.get("description_public")
    description_private = request.form.get("description_private")

    file = request.files.get("image")

    if not file:
        return jsonify({"error": "No file"}), 400

    filename = secure_filename(file.filename)
    filename = f"{int(datetime.now().timestamp())}_{filename}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
        INSERT INTO castings 
        (title, platform, city, description_public, description_private, image, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        title,
        platform,
        city,
        description_public,
        description_private,
        filename,
        datetime.now().strftime("%Y-%m-%d %H:%M")
    ))

    conn.commit()
    conn.close()

    return jsonify({"success": True})

# ==============================
# DELETE CASTING
# ==============================
@app.route("/api/castings/<int:id>", methods=["DELETE"])
def delete_casting(id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT image FROM castings WHERE id=?", (id,))
    row = c.fetchone()

    if row:
        image_path = os.path.join(UPLOAD_FOLDER, row[0])
        if os.path.exists(image_path):
            os.remove(image_path)

    c.execute("DELETE FROM castings WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return jsonify({"success": True})

# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    app.run(debug=True)

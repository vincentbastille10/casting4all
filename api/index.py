from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "/tmp/uploads"
DB = "/tmp/castings.db"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

@app.route("/")
def home():
    return "API RUNNING"

# GET CASTINGS
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
            "image": f"/api/uploads/{row[6]}",
            "created_at": row[7],
            "locked": True
        })

    return jsonify(castings)

# ADD CASTING (🔥 IMPORTANT : accepte FORM-DATA)
@app.route("/api/add-casting", methods=["POST"])
def add_casting():
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
        request.form.get("title"),
        request.form.get("platform"),
        request.form.get("city"),
        request.form.get("description_public"),
        request.form.get("description_private"),
        filename,
        datetime.now().strftime("%Y-%m-%d %H:%M")
    ))

    conn.commit()
    conn.close()

    return jsonify({"success": True})

# DELETE CASTING
@app.route("/api/delete-casting", methods=["POST"])
def delete_casting():
    data = request.get_json()
    index = data.get("index")

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id FROM castings ORDER BY id DESC")
    rows = c.fetchall()

    if index >= len(rows):
        return jsonify({"error": "Invalid index"}), 400

    casting_id = rows[index][0]

    c.execute("DELETE FROM castings WHERE id = ?", (casting_id,))
    conn.commit()
    conn.close()

    return jsonify({"success": True})

# SERVE IMAGE
@app.route("/api/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# RUN LOCAL
if __name__ == "__main__":
    app.run(debug=True)

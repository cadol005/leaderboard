from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

DB_NAME = "database.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            wins INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]

    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    existing_user = conn.execute(
        "SELECT * FROM users WHERE username = ? OR email = ?",
        (username, email)
    ).fetchone()

    if existing_user:
        conn.close()
        return jsonify({"error": "username or email exists"}), 400

    conn.execute(
        "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
        (username, email, hashed_password)
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "user registered successfully"}), 201

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()
    conn.close()

    if user and check_password_hash(user["password"], password):
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        return redirect(url_for("leaderboard"))

    return "Invalid username or password"

@app.route("/leaderboard")
def leaderboard():
    conn = get_db_connection()
    users = conn.execute(
        "SELECT username, wins FROM users ORDER BY wins DESC"
    ).fetchall()
    conn.close()
    return render_template("leaderboard.html", users=users)

@app.route("/add_win", methods=["POST"])
def add_win():
    data = request.get_json()
    username = data.get("username")

    conn = get_db_connection()
    conn.execute(
        "UPDATE users SET wins = wins + 1 WHERE username = ?",
        (username,)
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Win added"})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)

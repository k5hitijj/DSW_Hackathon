import sqlite3

import os

# Always resolve the absolute path to users.db relative to this file's location
DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")

def get_connection():
    return sqlite3.connect(DB_PATH)


def create_users_table():
    conn = get_connection()

    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    # Add chat history table: links each message to a user
    c.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            role TEXT,
            message TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_user(username, password_hash):
    conn = get_connection()

    c = conn.cursor()
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password_hash))
    conn.commit()
    conn.close()

def get_user(username):
    conn = get_connection()

    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    return user

def add_chat_message(username, role, message, timestamp):
    conn = get_connection()

    c = conn.cursor()
    c.execute("INSERT INTO chat_history (username, role, message, timestamp) VALUES (?, ?, ?, ?)",
              (username, role, message, timestamp))
    conn.commit()
    conn.close()

def get_chat_history(username):
    conn = get_connection()

    c = conn.cursor()
    c.execute("SELECT role, message, timestamp FROM chat_history WHERE username=? ORDER BY id ASC", (username,))
    history = c.fetchall()
    conn.close()
    return history

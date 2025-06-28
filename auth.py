import sqlite3
import hashlib
sqlite3.connect("users.db")
from db import get_connection


DB_PATH = "chat_history.db"

def hash_password(password):
    """Returns a SHA-256 hashed version of the password"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    """Verifies if provided password matches the hashed password"""
    return hash_password(password) == hashed

def get_user(username):
    """Retrieve user record from the database by username"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    return user

def add_user(username, hashed_password):
    """Add a new user record to the database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
    conn.commit()
    conn.close()

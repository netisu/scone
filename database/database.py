import sqlite3
import os

DB_FOLDER = "database"#just for organization, you/idk can change this later if you want to leave it on "main"
DB_NAME = "users.db"
DB_PATH = os.path.join(DB_FOLDER, DB_NAME)

def get_connection():
    os.makedirs(DB_FOLDER, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            netisuId INTEGER PRIMARY KEY,
            discordId INTEGER
        )
        """)
        conn.commit()

def add_user(netisu_id: int, discord_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO users (netisuId, discordId) VALUES (?, ?)",
            (netisu_id, discord_id)
        )
        conn.commit()


def remove_user(netisu_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM users WHERE netisuId = ?",
            (netisu_id,)
        )
        conn.commit()


def find_user(netisu_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE netisuId = ?",
            (netisu_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
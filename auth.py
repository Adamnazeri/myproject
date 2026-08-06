import sqlite3
import bcrypt

DB_PATH = "users.db"

DEPARTMENTS = ["IT", "Finance", "Human Resource", "Operations", "Marketing"]


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            dept TEXT,
            profile_pic BLOB
        )
    """)
    conn.commit()
    conn.close()


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())


class Auth:
    def __init__(self):
        init_db()

    def register(self, username, password, phone="", dept=""):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password, phone, dept) VALUES (?, ?, ?, ?)",
                (username, hash_password(password), phone, dept)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def check_password(self, username, password):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        if row is None:
            return False
        return verify_password(password, row[0])

    def get_user_info(self, username):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, phone, dept FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        if row is None:
            return None
        return {"id": row[0], "username": row[1], "phone": row[2], "dept": row[3]}

    def update_profile_pic(self, username, image_bytes):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET profile_pic = ? WHERE username = ?",
            (image_bytes, username)
        )
        conn.commit()
        conn.close()

    def get_profile_pic(self, username):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT profile_pic FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        if row is None or row[0] is None:
            return None
        return row[0]

    def update_profile(self, old_username, new_username, phone, dept):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE users SET username = ?, phone = ?, dept = ? WHERE username = ?",
                (new_username, phone, dept, old_username)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False   # new_username already taken by someone else
        finally:
            conn.close()

    def update_password(self, username, new_password):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET password = ? WHERE username = ?",
            (hash_password(new_password), username)
        )
        conn.commit()
        conn.close()
"""
Authentication service.
Passwords are NEVER stored in plain text — each password gets a random
salt, then is hashed with SHA-256 (via hashlib.pbkdf2_hmac, which is
purpose-built for password hashing and resistant to brute-force/rainbow
table attacks, unlike a plain sha256(password) call).
"""

import hashlib
import os
import binascii
import sqlite3

from services.database import Database


class AuthError(Exception):
    pass


def _hash_password(password: str, salt: bytes) -> str:
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return binascii.hexlify(dk).decode()


class AuthManager:
    def __init__(self, db: Database):
        self.db = db

    def register(self, username: str, password: str, role: str) -> None:
        username = username.strip()
        if not username or not password:
            raise AuthError("Username and password cannot be empty.")
        if role not in ("Admin", "Teacher", "Student"):
            raise AuthError("Invalid role.")

        salt = os.urandom(16)
        pwd_hash = _hash_password(password, salt)
        try:
            self.db.cursor.execute(
                "INSERT INTO users VALUES (?, ?, ?, ?)",
                (username, pwd_hash, binascii.hexlify(salt).decode(), role),
            )
            self.db.conn.commit()
        except sqlite3.IntegrityError:
            raise AuthError(f"Username '{username}' already exists.")

    def login(self, username: str, password: str) -> str:
        """Returns the user's role on success, raises AuthError on failure."""
        self.db.cursor.execute(
            "SELECT password_hash, salt, role FROM users WHERE username = ?",
            (username,),
        )
        row = self.db.cursor.fetchone()
        if row is None:
            raise AuthError("Invalid username or password.")

        stored_hash, salt_hex, role = row
        salt = binascii.unhexlify(salt_hex)
        if _hash_password(password, salt) != stored_hash:
            raise AuthError("Invalid username or password.")
        return role

    def has_any_user(self) -> bool:
        self.db.cursor.execute("SELECT COUNT(*) FROM users")
        return self.db.cursor.fetchone()[0] > 0

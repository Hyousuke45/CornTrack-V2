"""Prototype authentication using PBKDF2 password hashing."""
import hashlib, hmac, os
from database import db, now_text

def hash_password(password):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 240_000)
    return salt.hex() + "$" + digest.hex()

def verify_password(password, stored):
    try:
        salt_hex, digest_hex = stored.split("$", 1)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 240_000)
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False

def register(full_name, contact, password, municipality="", barangay="", farm_name=""):
    with db() as con:
        con.execute("INSERT INTO users(full_name,contact,password_hash,municipality,barangay,farm_name,created_at) VALUES(?,?,?,?,?,?,?)",
                    (full_name.strip(), contact.strip().lower(), hash_password(password), municipality.strip(), barangay.strip(), farm_name.strip(), now_text()))
        return con.execute("SELECT last_insert_rowid()").fetchone()[0]

def login(contact, password):
    with db() as con:
        row = con.execute("SELECT id,password_hash FROM users WHERE contact=?", (contact.strip().lower(),)).fetchone()
        if row and verify_password(password, row["password_hash"]):
            return row["id"]
    return None

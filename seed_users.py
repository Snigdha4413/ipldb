"""
Run this script ONCE after setting up your database to insert users with hashed passwords.

Usage:
    DATABASE_URL=your_postgres_url python seed_users.py

Or on Render: run it as a one-off job in the Shell tab.
"""

import os
from sqlalchemy import create_engine, text
from werkzeug.security import generate_password_hash

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

users = [
    {"username": "admin",   "password": "admin123", "role": "admin"},
    {"username": "client1", "password": "pass123",  "role": "client"},
    {"username": "client2", "password": "pass123",  "role": "client"},
]

with engine.connect() as conn:
    # Clear existing users
    conn.execute(text("DELETE FROM users"))

    for u in users:
        hashed = generate_password_hash(u["password"])
        conn.execute(
            text("INSERT INTO users (username, password, role) VALUES (:u, :p, :r)"),
            {"u": u["username"], "p": hashed, "r": u["role"]}
        )
        print(f"✅ Inserted user: {u['username']} ({u['role']})")

    conn.commit()
    print("\n✅ All users seeded successfully with hashed passwords.")

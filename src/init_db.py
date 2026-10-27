import os
import sqlite3

import bcrypt

INSTANCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "instance")

os.makedirs(os.path.join(INSTANCE, "uploads"), exist_ok=True)
db = sqlite3.connect(os.path.join(INSTANCE, "notes.db"))

db.executescript("""
DROP TABLE IF EXISTS notes;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash BLOB NOT NULL,
    reset_token TEXT
);

CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL REFERENCES users (id),
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    public INTEGER NOT NULL DEFAULT 0
);
""")

for username, password in [("alice", "alice-pass"), ("bob", "bob-pass")]:
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))

db.executemany("INSERT INTO notes (owner_id, title, body, public) VALUES (?, ?, ?, ?)", [
    (1, "CSC 4028 exam topics", "<b>Static testing</b>, code review, buffer overflows", 1),
    (1, "Private: scholarship essay", "My essay draft and my student ID 900123456", 0),
    (2, "Lab partner contacts", "Alice: 303-555-0101", 0),
])
db.commit()

with open(os.path.join(INSTANCE, "uploads", "syllabus.txt"), "w") as file:
    file.write("CSC 4028 Secure Software Development syllabus\n")

print("Database created with users alice/alice-pass and bob/bob-pass")

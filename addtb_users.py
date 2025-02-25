import sqlite3
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
conn = sqlite3.connect("D://SQLITE/yantek.db")
cursor = conn.cursor()

# Buat tabel users jika belum ada
cursor.execute("""
    CREATE TABLE IF NOT EXISTS tb_user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        keterangan TEXT
    )
""")

# Tambahkan user default (username: admin, password: admin123)
hashed_password = bcrypt.generate_password_hash("admin123").decode("utf-8")
cursor.execute("INSERT OR IGNORE INTO tb_user (username, password) VALUES (?, ?)", ("admin", hashed_password))

conn.commit()
conn.close()

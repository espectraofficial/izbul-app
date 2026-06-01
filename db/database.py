import sqlite3

DB_NAME = "jobs.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site TEXT,
        company TEXT,
        title TEXT,
        url TEXT UNIQUE
    )
    """)

    conn.commit()
    conn.close()


def add_favorite(job):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("""
        INSERT INTO favorites (site, company, title, url)
        VALUES (?, ?, ?, ?)
        """, (job.site, job.company, job.title, job.url))
        conn.commit()
        return True  # 🔥 başarılı
    except sqlite3.IntegrityError:
        return False  # zaten var

    finally:
        conn.close()


def remove_favorite(url):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM favorites WHERE url = ?", (url,))
    conn.commit()
    conn.close()


def get_favorites():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT site, company, title, url FROM favorites")
    rows = cursor.fetchall()

    conn.close()
    return rows
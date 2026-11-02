import sqlite3

def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS giveaway (
            user_id INTEGER PRIMARY KEY,
            username TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_giveaway_user(user_id, username):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO giveaway (user_id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()
        success = cursor.rowcount > 0
    except Exception:
        success = False
    finally:
        conn.close()
    return success

def get_random_winner():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username FROM giveaway ORDER BY RANDOM() LIMIT 1")
    winner = cursor.fetchone()
    conn.close()
    return winner

import sqlite3


def init_db(database="weather.db"):
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            search_count INTEGER NOT NULL DEFAULT 1
        )
    """
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()

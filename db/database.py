import sqlite3

def get_connection(path):
    conn=sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def create_table(path):
    try:
        connection=get_connection(path)

        cursor=connection.cursor()

        cursor.execute("""
                CREATE TABLE IF NOT EXISTS chats(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
        """)

        cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (chat_id) REFERENCES chats(id)
                )
        """) 
    finally:
        connection.commit()
        connection.close()

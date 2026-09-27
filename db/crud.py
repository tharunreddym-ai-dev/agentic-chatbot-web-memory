def create_chat(connection,name):
    cursor=connection.cursor()

    cursor.execute("""
            INSERT INTO chats(name,created_at)
            VALUES (?,datetime('now'))""",
            (name,)
            )

    chat_id=cursor.lastrowid
    connection.commit()
    return chat_id

def list_chats(connection):
    cursor=connection.cursor()

    cursor.execute("""
            SELECT id,name,created_at
            FROM chats
            ORDER BY id
    """)

    rows=cursor.fetchall()

    return rows

def add_message(connection,chat_id,role,content):
    cursor=connection.cursor()
    cursor.execute("""
            INSERT INTO messages(chat_id,role,content,timestamp)
            VALUES (?,?,?,datetime('now'))""",
            (chat_id,role,content))

    connection.commit()

def get_latest_messages(connection,chat_id,n):
    cursor=connection.cursor()
    cursor.execute("""
            SELECT role,content FROM messages 
            WHERE chat_id=? 
            ORDER BY id DESC LIMIT ?""",
            (chat_id,n))
    
    rows=cursor.fetchall()
    return list(reversed(rows))

def get_message_count(connection,chat_id):
    cursor=connection.cursor()
    cursor.execute("""
            SELECT COUNT(*) 
            FROM messages 
            WHERE chat_id=?""",
            (chat_id,))
    
    return cursor.fetchone()[0]

def delete_oldest_messages(connection, chat_id, count):
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM messages
        WHERE id IN (
            SELECT id
            FROM messages
            WHERE chat_id = ?
            ORDER BY id ASC
            LIMIT ?)""", 
        (chat_id, count))

    connection.commit()

def get_oldest_messages(connection, chat_id, count) -> list:
    cursor=connection.cursor()

    cursor.execute("""
        SELECT role,content 
        FROM messages
        WHERE chat_id=?
        ORDER BY id ASC
        LIMIT ?"""
        ,(chat_id,count))

    return cursor.fetchall()

def delete_messages_of_chat(connection,chat_id):
    cursor=connection.cursor()

    cursor.execute("""
        DELETE FROM messages
        WHERE chat_id=?""",
        (chat_id,))

    connection.commit()

def delete_chat(connection,chat_id):
    cursor=connection.cursor()

    cursor.execute("""
        DELETE FROM chats
        WHERE id=?""",
        (chat_id,))

    connection.commit()
def get_all_messages(connection,chat_id):
    cursor=connection.cursor()
    cursor.execute("""
            SELECT role,content,timestamp
            FROM messages
            WHERE chat_id=?
            ORDER BY id ASC""",
            (chat_id,))

    return cursor.fetchall()

from fastapi import APIRouter,HTTPException
from config import SQLITE_CONNECTION_PATH
from db.database import get_connection
from db.crud import create_chat,list_chats,delete_chat,delete_messages_of_chat,get_all_messages
from vectorstore.qdrant_client import get_qdrant_client
from vectorstore.collections import create_memory_collection,delete_memory_collection
from agent.chat import chat

router=APIRouter()

MAX_CHUNKS=150

_qdrant_client=get_qdrant_client()

def _get_db_connection():
    return get_connection(path=SQLITE_CONNECTION_PATH)

def _chat_exists(connection,chat_id:int)->bool:
    chats=list_chats(connection=connection)
    return any(row[0]==chat_id for row in chats)

@router.post("/chats")
def create_new_chat(payload:dict):
    name=payload.get("name")

    if not name:
        raise HTTPException(status_code=400,detail="chat name is required")

    connection=_get_db_connection()

    try:
        chat_id=create_chat(connection=connection,name=name)

        try:
            create_memory_collection(client=_qdrant_client,chat_id=chat_id)

        except Exception as e:
            delete_chat(connection=connection,chat_id=chat_id)
            raise HTTPException(status_code=500,detail=f"Chat created in database but Qdrant Collection Failed-{e}")

        return {"id":chat_id,"name":name}

    finally:
        connection.close()

@router.get("/chats")
def get_all_chats():
    connection=_get_db_connection()

    try:
        rows=list_chats(connection=connection)
        return[
            {
                "id":row[0],"name":row[1],"created_at":row[2]
            }
            for row in rows
        ]

    finally:
        connection.close()

@router.get("/chats/{chat_id}/messages")
def get_chat_messages(chat_id:int):
    connection=_get_db_connection()

    try:
        if not _chat_exists(connection=connection,chat_id=chat_id):
            raise HTTPException(status_code=404,detail=f"Chat {chat_id} not Found")

        rows=get_all_messages(connection=connection,chat_id=chat_id)
        return [
            {"role":row[0],"content":row[1],"timestamp":row[2]}
            for row in rows
        ]

    finally:
        connection.close()

@router.post("/chats/{chat_id}/chat")
def chat_with_user(chat_id:int,payload:dict):
    user_input=payload.get("message")

    if not user_input:
        raise HTTPException(status_code=400,detail="message is required")
    connection=_get_db_connection()

    try:
        if not _chat_exists(connection=connection,chat_id=chat_id):
            raise HTTPException(status_code=404,detail=f"Chat {chat_id} not Found")

        try:
            answer=chat(connection=connection,client=_qdrant_client,chat_id=chat_id,user_input=user_input)

        except Exception as e:
            raise HTTPException(status_code=500,detail=f"Chat Failed:{e}")

        return {"answer":answer}

    finally:
        connection.close()

@router.delete("/chats/{chat_id}")
def remove_chat(chat_id:int):
    connection=_get_db_connection()
    try:
        if not _chat_exists(connection=connection,chat_id=chat_id):
            raise HTTPException(status_code=404,detail=f"Chat {chat_id} not found")
        
        delete_messages_of_chat(connection=connection,chat_id=chat_id)
        delete_chat(connection=connection,chat_id=chat_id)

        try:
            delete_memory_collection(client=_qdrant_client,chat_id=chat_id)
        except Exception as e:
            raise HTTPException(status_code=500,detail=f"Chat deleted in database but failed for collection deletion: {e}")

        return {"status":"deleted","chat_id":chat_id}
    finally:
        connection.close()

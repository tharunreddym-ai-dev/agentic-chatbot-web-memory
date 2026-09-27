from langchain_groq import ChatGroq
from config import GROQ_CHAT_MODEL,GROQ_API_KEY,RECENT_MESSAGES_LIMIT,EMBEDDING_MODEL_DIMENSION
from qdrant_client.models import PointStruct
from uuid import uuid4
from db.crud import get_oldest_messages,get_message_count,delete_oldest_messages
from vectorstore.ingest import embed_chunks,chunk_text
from vectorstore.collections import get_memory_collection_name
from agent.prompts import summary_prompt

COMPACT_COUNT=(3*RECENT_MESSAGES_LIMIT)//4
MAX_TRIES=5

def format_chat_history(messages) -> str:
    if not messages:
        return "No Recent Conversations Yet"


    return "\n".join([f"{role}:{content}" for role,content in messages])

def summarize_messages(messages):

    formatted_messages=format_chat_history(messages=messages)

    llm=ChatGroq(model=GROQ_CHAT_MODEL,
                 api_key=GROQ_API_KEY,
                 temperature=0.1,
                 max_retries=MAX_TRIES,
                )

    prompt=summary_prompt.invoke({"conversation":formatted_messages })

    response=llm.invoke(prompt)

    summary = response.content.strip()

    if "<think>" in summary:
        if "</think>" in summary:
            summary = summary.split("</think>", 1)[1].strip()
        else:
            summary = summary.split("<think>", 1)[0].strip()
            
    return summary

def store_memory(client,chat_id,summary):
    memory_name=get_memory_collection_name(chat_id=chat_id)

    chunks=chunk_text(summary)

    embeddings=embed_chunks(chunks=chunks,input_type="passage")
    if len(embeddings[0])==EMBEDDING_MODEL_DIMENSION:
        points=[]

        for i,(chunk,embedding) in enumerate(zip(chunks,embeddings)):
            points.append(
                PointStruct(id=str(uuid4()),
                            vector=embedding,
                            payload={
                                "text":chunk,
                                "chunk_index":i,
                                "source":"past_memory"
                            }
                )
            )

        client.upsert(
            collection_name=memory_name,
            points=points
        )
    else:
        raise Exception("Embedding Dimension Mismatch")

def compact_if_needed(connection, client, chat_id):
    count=get_message_count(
        connection=connection,
        chat_id=chat_id
    )

    if count<RECENT_MESSAGES_LIMIT:
        return

    messages=get_oldest_messages(connection=connection,
                                 chat_id=chat_id,
                                 count=COMPACT_COUNT)
    try:
        summary=summarize_messages(messages)

        store_memory(client=client,chat_id=chat_id,summary=summary)

        delete_oldest_messages(connection=connection,chat_id=chat_id,count=COMPACT_COUNT)

    except Exception as e:
        raise Exception(f"Error {e}")

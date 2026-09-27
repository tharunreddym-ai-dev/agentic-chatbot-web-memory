from qdrant_client.models import VectorParams,Distance
from config import EMBEDDING_MODEL_DIMENSION
def get_memory_collection_name(chat_id):
    memory_name=f"{chat_id}_memory"
    return memory_name

def create_collection(client,collection_name):
    if client.collection_exists(collection_name):
        return

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=EMBEDDING_MODEL_DIMENSION,
            distance=Distance.COSINE
        )
    )


def create_memory_collection(client,chat_id):
    memory_name=get_memory_collection_name(chat_id)

    create_collection(client=client,collection_name=memory_name)

def delete_memory_collection(client,chat_id):
    memory_name=get_memory_collection_name(chat_id=chat_id)

    if client.collection_exists(memory_name):
        client.delete_collection(memory_name)

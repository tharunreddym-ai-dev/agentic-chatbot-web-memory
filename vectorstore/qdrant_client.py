from qdrant_client import QdrantClient
from config import QDRANT_PATH

def get_qdrant_client():
    return QdrantClient(path=QDRANT_PATH)

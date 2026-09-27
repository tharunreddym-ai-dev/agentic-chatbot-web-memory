from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import EMBEDDING_MODEL,EMBEDDING_MODEL_URL,NVIDIA_API_KEY
from vectorstore.collections import create_memory_collection
import requests
import time

CHUNK_SIZE=500
CHUNK_OVERLAP=100
MAX_TRIES=3
def chunk_text(text):
    splitter=RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len
    )

    chunks=splitter.split_text(text)

    return chunks

def embed_chunks(chunks,input_type):
    headers={
        "Authorization":f"Bearer {NVIDIA_API_KEY}",
        "Content-Type":"application/json"
    }

    body={
        "model":EMBEDDING_MODEL,
        "input":chunks,
        "encoding_format":"float",
        "input_type":input_type
    }

    for attempt in range(MAX_TRIES):
        try:
            response=requests.post(url=EMBEDDING_MODEL_URL,headers=headers,json=body)
            if response.status_code!=200:
                raise Exception(f"API Error {response.text} with code {response.status_code}")
            data=response.json()

            if "data" not in data:
                raise Exception(f"Unexpected response {data}")
            
            embds=[item["embedding"] for item in data["data"]]
            return embds
        
        except Exception as e:
            if attempt==MAX_TRIES-1:
                raise e
            wait=2**attempt
            time.sleep(wait)
            print(f"Attempt- {attempt+1} Failed, Retrying in {wait} Seconds...")

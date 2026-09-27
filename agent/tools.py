from langchain_core.tools import Tool
from vectorstore.ingest import embed_chunks
from vectorstore.collections import get_memory_collection_name
from tavily import TavilyClient
from config import TAVILY_API_KEY

TOP_K=3
tavily=TavilyClient(api_key=TAVILY_API_KEY)

def embed_query(query_text) -> list[float]:
    return embed_chunks(chunks=[query_text],input_type="query")[0]

def search_collection(client, collection_name, query_text, top_k) -> list[str]:
    
    query_vector=embed_query(query_text=query_text)

    results=client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=top_k,
        with_payload=True
    ).points

    retrieved_chunks=[]

    if not results:
        return ["No relevant information was found."]

    for i,result in enumerate(results,start=1):
        retrieved_chunks.append(f'Result:{i} Content:{result.payload["text"]} Source:{result.payload["source"]}')
    return retrieved_chunks

def make_web_search_tool():
    def web_search(query:str):
        try:
            if not query or not query.strip():
                return "Query Can't be Empty"
            result=tavily.search(
                query=query,
                search_depth="basic",
                max_results=2
                )
            return [c["content"] for c in result["results"]]

        except Exception as e:
            return f"Tool Error: {e}"
    
    return Tool(
        name="web_search_tool",
        func=web_search,
        description="""This Tool is used to Search Information From the Web
                        Use This When you need
                        -Current Events
                        -Recent Information
                        -General Information from Web
                        -Live Information
                        -And Anything which is recent and which is outdated from your knowledge"""
    )
        
def make_memory_tool(client, chat_id):
    memory_name=get_memory_collection_name(chat_id=chat_id)
    try:
        def _search(query: str) -> str:
            if not client.collection_exists(memory_name):
                raise Exception("No Memory Yet")
            if client.count(memory_name).count==0:
                return "There is no long-term memory yet for this conversation"
            results=search_collection(client=client,collection_name=memory_name,query_text=query,top_k=TOP_K)
            return "\n\n".join(results)

    except Exception as e:
        return f"Error {e} While Searching."
    return Tool(name="long_term_memory_rag_search", 
                func=_search, 
                description="""Use this when the user references or asks about something from earlier in this 
                               conversation that isn't visible in your current context.
                               This conversation will be summarized so phrase a query accordingly and it will be 
                               summarized in chronologically order
                               Do not use this tool for questions related Web Search Tool.
                               For uploaded-document questions, use document_rag_search instead.""")

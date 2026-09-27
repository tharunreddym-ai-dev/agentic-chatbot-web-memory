from langchain_classic.agents import create_react_agent,AgentExecutor
from agent.prompts import react_prompt
from agent.tools import make_memory_tool,make_web_search_tool
from config import GEMINI_API_KEY,GEMINI_CHAT_MODEL
from langchain_google_genai import ChatGoogleGenerativeAI

TEMPERATURE=0.2
MAX_ITERATIONS=10

llm=ChatGoogleGenerativeAI(
    model=GEMINI_CHAT_MODEL,
    google_api_key=GEMINI_API_KEY,
    temperature=TEMPERATURE
)

def build_executor(client,chat_id):
    tools=[make_web_search_tool(),make_memory_tool(client,chat_id)]

    agent=create_react_agent(
        llm=llm,
        prompt=react_prompt,
        tools=tools
    )

    executor=AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=MAX_ITERATIONS,
        max_execution_time=30,
    )

    return executor

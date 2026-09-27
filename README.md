# Agentic Chat — ReAct agent with web search + tiered long-term memory

## Overview

Agentic ChatBot is a full-stack Agentic AI chat application built around a Gemini-powered ReAct agent. It combines web search with persistent, tiered conversation memory so the agent can use both recent chat context and older information stored as vector memories.

The backend is built with FastAPI and LangChain. The agent uses two tools: Tavily for web search and Qdrant for long-term memory retrieval. Recent conversation messages are stored in SQLite. When a chat grows beyond `RECENT_MESSAGES_LIMIT`, older messages are summarized using Groq, converted into embeddings through the NVIDIA embeddings API, stored in a per-chat Qdrant collection, and removed from SQLite.

The frontend is a separate Streamlit application that communicates with the backend only through HTTP. This keeps the frontend and backend independently runnable and deployable.

## Project structure

```text
.
├── main.py                  # FastAPI app entrypoint
├── config.py                # env var loading/validation
├── requirements.txt         # backend dependencies
├── .env.example
├── api/
│   └── routes.py            # HTTP endpoints
├── agent/
│   ├── build_agent.py       # builds the Gemini ReAct AgentExecutor
│   ├── chat.py              # orchestrates one chat turn
│   ├── compaction.py        # summarize + move old messages to vector memory
│   ├── prompts.py           # ReAct + summarization prompt templates
│   └── tools.py             # web search tool + long-term memory search tool
├── db/
│   ├── database.py          # SQLite connection + schema
│   └── crud.py              # chat/message queries
├── vectorstore/
│   ├── qdrant_client.py     # local Qdrant client
│   ├── collections.py       # per-chat memory collection helpers
│   └── ingest.py            # chunking + NVIDIA embeddings call
└── frontend/                # Streamlit app — separate process, own deps
    ├── requirements.txt     # streamlit + requests only
    ├── app.py               # sidebar (chat switcher) + chat panel
    ├── api_client.py        # thin HTTP client — never imports backend code
    └── styles.py            # theme CSS injected into the page
```

The backend and frontend are two independent processes talking over plain HTTP — the frontend never imports a backend module, and the backend has no idea a Streamlit app exists. Each has its own `requirements.txt`.

## Setup

### Backend

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Frontend

A separate virtual environment is recommended because the frontend has its own, much smaller dependency set.

```bash
cd frontend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Required backend `.env` values

See `.env.example`:

- `GEMINI_API_KEY`, `GEMINI_CHAT_MODEL` — the agent's chat model
- `GROQ_API_KEY`, `GROQ_CHAT_MODEL` — used only for compaction summaries
- `NVIDIA_API_KEY`, `EMBEDDING_MODEL`, `EMBEDDING_MODEL_URL`, `EMBEDDING_MODEL_DIMENSION` — embeddings for long-term memory. **`EMBEDDING_MODEL_DIMENSION` must exactly match the dimension your embedding model actually returns**, or `compaction.py` will raise `Embedding Dimension Mismatch` the first time a chat compacts.
- `QDRANT_PATH` — local on-disk Qdrant storage path
- `SQLITE_CONNECTION_PATH` — local SQLite file path
- `RECENT_MESSAGES_LIMIT` — how many messages a chat can hold before compaction fires

The frontend needs no `.env` file — it just needs to know where the backend is.

## Running

### Backend

```bash
uvicorn main:app --reload --port 8000
```

or:

```bash
python -m uvicorn main:app
```

### Frontend

```bash
cd frontend
streamlit run app.py
```

or:

```bash
python -m streamlit run app.py
```

By default the frontend calls the backend at `http://localhost:8000`. If yours runs somewhere else, set `BACKEND_URL` before launching:

```bash
BACKEND_URL=http://localhost:9000 streamlit run app.py
```

Streamlit opens its own browser tab, usually at `http://localhost:8501`.

## API

| Method | Path | Body | Notes |
|--------|------|------|-------|
| POST | `/chats` | `{"name": str}` | creates a chat + its Qdrant memory collection |
| GET | `/chats` | — | list chats, ascending by id |
| GET | `/chats/{chat_id}/messages` | — | full message history for a chat |
| POST | `/chats/{chat_id}/chat` | `{"message": str}` | runs the agent, returns `{"answer": str}` |
| DELETE | `/chats/{chat_id}` | — | deletes the chat, its messages, and its Qdrant collection |

## How memory works

The project uses a two-tier memory design:

1. **Recent memory — SQLite**
   Stores the active conversation messages so the agent can use the latest context directly.

2. **Long-term memory — Qdrant**
   When the conversation exceeds `RECENT_MESSAGES_LIMIT`, the older messages are summarized with Groq, embedded with the NVIDIA embeddings API, and stored in that chat's Qdrant collection. Those old raw messages are then removed from SQLite.

3. **Memory retrieval**
   The ReAct agent can search the chat's Qdrant collection through its long-term memory tool when older context is relevant.

This keeps the active conversation smaller while still allowing the agent to retrieve information from earlier parts of the chat.

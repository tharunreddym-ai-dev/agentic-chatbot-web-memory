from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import SQLITE_CONNECTION_PATH
from db.database import get_connection
from db.database import create_table
from api.routes import router

app = FastAPI(title="Agentic Bot with Long Term Memory")

# NOTE: added for the frontend (not one of the previously reviewed bugs).
# The frontend is served from a different origin/port than this API, so the
# browser needs CORS allowed or every fetch() call from it will be blocked.
# allow_origins=["*"] is fine for a local single-user tool; tighten it if
# you ever deploy this somewhere shared.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def on_startup():
    create_table(path=SQLITE_CONNECTION_PATH)

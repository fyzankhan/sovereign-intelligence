
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mysql_setup import router as mysql_router
from chat import router as chat_router
from rag import router as rag_router

load_dotenv()

app = FastAPI(
    title="Local LLM API",
    version="1.5.0",
)

ALLOW_ORIGIN = os.environ["ALLOW_ORIGINS"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOW_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mysql_router)
app.include_router(chat_router)
app.include_router(rag_router)

@app.get("/health")
async def health():
    return {"status": "ok"}

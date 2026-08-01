from dotenv import load_dotenv
load_dotenv()

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import connect_db, disconnect_db
from app.routers import webhooks

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="LeadFlow", description="Автоматизация захвата и обработки лидов")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # для продакшена сузить до домена лендинга
    allow_methods=["POST"],
    allow_headers=["*"],
)

app.include_router(webhooks.router)


@app.on_event("startup")
async def on_startup():
    await connect_db()


@app.on_event("shutdown")
async def on_shutdown():
    await disconnect_db()


@app.get("/health")
async def health():
    return {"status": "ok"}

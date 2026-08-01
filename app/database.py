import os

from databases import Database
from sqlalchemy import (
    Column, DateTime, Integer, MetaData, String, Table, create_engine, func,
)

# Теперь по умолчанию используется SQLite — отдельный файл leadflow.db,
# без необходимости ставить Docker и Postgres. Если позже понадобится Postgres,
# достаточно поменять DATABASE_URL в .env на postgresql://...
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./leadflow.db")

database = Database(DATABASE_URL)
metadata = MetaData()

leads = Table(
    "leads",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False),
    Column("phone", String, nullable=False, index=True),
    Column("phone_hash", String, nullable=False, index=True),
    Column("source", String, nullable=False),
    Column("utm_source", String, nullable=True),
    Column("utm_medium", String, nullable=True),
    Column("utm_campaign", String, nullable=True),
    Column("budget", String, nullable=True),
    Column("project_type", String, nullable=True),
    Column("bitrix_deal_id", String, nullable=True),
    Column("sync_status", String, nullable=False, default="pending"),  # pending|synced|failed
    Column("repeat_contacts", Integer, nullable=False, default=0),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)


def create_tables() -> None:
    """Создаёт таблицы при первом запуске, если их ещё нет (работает и для SQLite, и для Postgres)."""
    engine = create_engine(DATABASE_URL)
    metadata.create_all(engine)


async def connect_db():
    create_tables()
    await database.connect()


async def disconnect_db():
    await database.disconnect()

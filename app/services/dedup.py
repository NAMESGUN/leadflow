import hashlib
from datetime import datetime, timedelta, timezone

from app.database import database, leads

DEDUP_WINDOW_HOURS = 24


def hash_phone(phone: str) -> str:
    return hashlib.sha256(phone.encode()).hexdigest()


async def find_duplicate(phone: str) -> dict | None:
    """Ищет лид с тем же телефоном за последние DEDUP_WINDOW_HOURS часов."""
    phone_hash = hash_phone(phone)
    window_start = datetime.now(timezone.utc) - timedelta(hours=DEDUP_WINDOW_HOURS)

    query = leads.select().where(
        (leads.c.phone_hash == phone_hash) & (leads.c.created_at > window_start)
    ).order_by(leads.c.created_at.desc())

    result = await database.fetch_one(query)
    return dict(result._mapping) if result else None


async def register_repeat_contact(lead_id: int) -> None:
    query = leads.update().where(leads.c.id == lead_id).values(
        repeat_contacts=leads.c.repeat_contacts + 1
    )
    await database.execute(query)

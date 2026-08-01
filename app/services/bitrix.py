import asyncio
import logging
import os

import httpx

from app.database import database, leads

logger = logging.getLogger("leadflow.bitrix")

BITRIX_WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL", "")
MAX_ATTEMPTS = 3


class BitrixApiError(Exception):
    pass


async def create_bitrix_lead(lead: dict) -> str:
    """Создаёт лид в Bitrix24 через REST API входящего вебхука."""
    payload = {
        "fields": {
            "TITLE": f"Заявка с сайта: {lead['project_type'] or 'не указан'}",
            "NAME": lead["name"],
            "PHONE": [{"VALUE": lead["phone"], "VALUE_TYPE": "WORK"}],
            "SOURCE_ID": "WEB" if lead["source"] == "form" else "OTHER",
            "UTM_SOURCE": lead.get("utm_source"),
            "UTM_MEDIUM": lead.get("utm_medium"),
            "UTM_CAMPAIGN": lead.get("utm_campaign"),
            "COMMENTS": f"Бюджет: {lead.get('budget')}, тип объекта: {lead.get('project_type')}",
        }
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(f"{BITRIX_WEBHOOK_URL}crm.lead.add.json", json=payload)

    data = response.json()
    if "result" not in data:
        raise BitrixApiError(data.get("error_description", "Unknown Bitrix24 error"))

    return str(data["result"])


async def forward_to_bitrix(lead_id: int, attempt: int = 1) -> None:
    """Отправляет лид в Bitrix24 с экспоненциальным ретраем при сбое."""
    query = leads.select().where(leads.c.id == lead_id)
    lead = await database.fetch_one(query)
    if lead is None:
        logger.error("Lead %s not found for Bitrix sync", lead_id)
        return

    try:
        deal_id = await create_bitrix_lead(dict(lead._mapping))
        await database.execute(
            leads.update().where(leads.c.id == lead_id).values(
                bitrix_deal_id=deal_id, sync_status="synced"
            )
        )
        logger.info("Lead %s synced to Bitrix24 as deal %s", lead_id, deal_id)
    except (BitrixApiError, httpx.HTTPError) as exc:
        logger.warning("Bitrix sync failed for lead %s (attempt %s): %s", lead_id, attempt, exc)
        if attempt < MAX_ATTEMPTS:
            await asyncio.sleep(2 ** attempt)
            await forward_to_bitrix(lead_id, attempt + 1)
        else:
            await database.execute(
                leads.update().where(leads.c.id == lead_id).values(sync_status="failed")
            )
            logger.error("Lead %s permanently failed to sync to Bitrix24", lead_id)

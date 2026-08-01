from fastapi import APIRouter, BackgroundTasks

from app.database import database, leads
from app.models.schemas import LeadPayload, LeadResponse
from app.services.bitrix import forward_to_bitrix
from app.services.dedup import find_duplicate, hash_phone, register_repeat_contact

router = APIRouter(prefix="/webhook", tags=["webhooks"])


async def process_lead(payload: LeadPayload, bg: BackgroundTasks) -> LeadResponse:
    existing = await find_duplicate(payload.phone)

    if existing:
        await register_repeat_contact(existing["id"])
        return LeadResponse(status="accepted", lead_id=existing["id"], is_duplicate=True)

    query = leads.insert().values(
        name=payload.name,
        phone=payload.phone,
        phone_hash=hash_phone(payload.phone),
        source=payload.source,
        utm_source=payload.utm_source,
        utm_medium=payload.utm_medium,
        utm_campaign=payload.utm_campaign,
        budget=payload.budget,
        project_type=payload.project_type,
        sync_status="pending",
        repeat_contacts=0,
    )
    lead_id = await database.execute(query)

    bg.add_task(forward_to_bitrix, lead_id)

    return LeadResponse(status="accepted", lead_id=lead_id, is_duplicate=False)


@router.post("/form", response_model=LeadResponse)
async def receive_form_lead(payload: LeadPayload, bg: BackgroundTasks):
    payload.source = "form"
    return await process_lead(payload, bg)


@router.post("/telegram", response_model=LeadResponse)
async def receive_bot_lead(payload: LeadPayload, bg: BackgroundTasks):
    payload.source = "telegram_bot"
    return await process_lead(payload, bg)
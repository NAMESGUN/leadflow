from pydantic import BaseModel, field_validator


class LeadPayload(BaseModel):
    """Данные лида, приходящие из формы на лендинге или от Telegram-бота."""

    name: str
    phone: str
    source: str  # "form" | "telegram_bot"
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    budget: str | None = None
    project_type: str | None = None
    raw_payload: dict = {}

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, v: str) -> str:
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) < 10:
            raise ValueError("Номер телефона слишком короткий")
        return digits[-10:]

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Имя не может быть пустым")
        return v


class LeadResponse(BaseModel):
    status: str
    lead_id: int
    is_duplicate: bool

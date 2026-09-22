import logging

from fastapi import Depends, FastAPI, HTTPException, Request

from app.bitrix_client import BitrixApiError, BitrixClient
from app.config import settings
from app.schemas import LeadIn, LeadOut, LeadStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bitrix24-lead-sync")

app = FastAPI(title="Bitrix24 Lead Sync")


def get_client() -> BitrixClient:
    return BitrixClient(settings.bitrix_webhook_url)


@app.post("/leads", response_model=LeadOut, status_code=201)
def create_lead(lead: LeadIn, client: BitrixClient = Depends(get_client)) -> LeadOut:
    """Принимает заявку с сайта и создаёт лид в CRM Bitrix24."""
    fields = {
        "TITLE": f"Заявка с сайта: {lead.name}",
        "NAME": lead.name,
        "PHONE": [{"VALUE": lead.phone, "VALUE_TYPE": "WORK"}],
        "SOURCE_ID": lead.source,
        "COMMENTS": lead.comment or "",
    }
    if lead.email:
        fields["EMAIL"] = [{"VALUE": lead.email, "VALUE_TYPE": "WORK"}]

    try:
        bitrix_id = client.add_lead(fields)
    except BitrixApiError as exc:
        logger.error("Bitrix24 create lead failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return LeadOut(bitrix_id=bitrix_id)


@app.get("/leads/{lead_id}", response_model=LeadStatus)
def get_lead(lead_id: int, client: BitrixClient = Depends(get_client)) -> LeadStatus:
    try:
        leads = client.list_leads(filter_={"ID": lead_id})
    except BitrixApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if not leads:
        raise HTTPException(status_code=404, detail="Lead not found")

    raw = leads[0]
    return LeadStatus(
        id=int(raw["ID"]),
        title=raw.get("TITLE", ""),
        status=raw.get("STATUS_ID", ""),
        name=raw.get("NAME"),
        phone=(raw.get("PHONE") or [{}])[0].get("VALUE"),
        email=(raw.get("EMAIL") or [{}])[0].get("VALUE"),
    )


@app.post("/webhook/bitrix")
async def bitrix_event(request: Request) -> dict:
    """Принимает исходящий вебхук Bitrix24 (например ONCRMLEADUPDATE).

    Bitrix24 шлёт application/x-www-form-urlencoded с полями
    event, data[FIELDS][ID], auth[application_token].
    """
    form = await request.form()

    token = form.get("auth[application_token]")
    if settings.bitrix_outgoing_token and token != settings.bitrix_outgoing_token:
        raise HTTPException(status_code=403, detail="Invalid application token")

    event = form.get("event", "UNKNOWN")
    lead_id = form.get("data[FIELDS][ID]")
    logger.info("Bitrix24 event received: %s lead_id=%s", event, lead_id)

    return {"status": "ok"}

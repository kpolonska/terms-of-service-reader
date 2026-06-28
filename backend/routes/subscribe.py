from fastapi import APIRouter
from pydantic import BaseModel

from services.subscription_service import subscribe, unsubscribe, get_subscriptions

router = APIRouter()


class SubscribeRequest(BaseModel):
    domain: str


@router.post("/subscribe")
def subscribe_domain(req: SubscribeRequest):
    subscribe(req.domain)
    return {"ok": True}


@router.delete("/subscribe/{domain}")
def unsubscribe_domain(domain: str):
    unsubscribe(domain)
    return {"ok": True}


@router.get("/subscriptions")
def list_subscriptions():
    return {"domains": get_subscriptions()}

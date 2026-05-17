from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.risk_engine import calculate_risk_score
from app.core.database import log_transaction

router = APIRouter()

class TransactionRequest(BaseModel):
    phone_hash: str
    amount: float
    recipient_phone_hash: str
    location_tower: Optional[str] = None
    channel: Optional[str] = "USSD"
    sim_swap_minutes_ago: Optional[int] = None
    gnn_fraud_score: Optional[float] = None

class RiskResponse(BaseModel):
    risk_score: int
    decision: str
    reason: str

@router.post("/risk-score", response_model=RiskResponse)
async def calculate_risk(transaction: TransactionRequest):
    result = calculate_risk_score(transaction.dict())

    # Log to Supabase
    log_transaction(
        user_id=None,
        amount=transaction.amount,
        recipient_phone_hash=transaction.recipient_phone_hash,
        sim_swap_minutes_ago=transaction.sim_swap_minutes_ago,
        risk_score=result["risk_score"],
        decision=result["decision"],
        reason=result["reason"],
        location_tower=transaction.location_tower
    )

    return result


@router.get("/transactions/recent")
async def get_recent():
    from app.core.database import get_recent_transactions
    return get_recent_transactions()
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.risk_engine import calculate_risk_score

router = APIRouter()

class TransactionRequest(BaseModel):
    phone_hash: str
    amount: float
    recipient_phone_hash: str
    location_tower: Optional[str] = None
    channel: Optional[str] = "USSD"  # USSD | MOBILE_APP | BRANCH
    sim_swap_minutes_ago: Optional[int] = None
    gnn_fraud_score: Optional[float] = None  # Matshepo's input (0-100)

class RiskResponse(BaseModel):
    risk_score: int
    decision: str   # ALLOW | STEP_UP | BLOCK
    reason: str

@router.post("/risk-score", response_model=RiskResponse)
async def calculate_risk(transaction: TransactionRequest):
    result = calculate_risk_score(transaction.dict())
    return result
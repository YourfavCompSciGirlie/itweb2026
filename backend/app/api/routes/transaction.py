from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import random

router = APIRouter()

class CustomerProfile(BaseModel):
    customer_id: str
    phone_number: str
    avg_transaction_amount: float
    typical_recipients: List[str] = []
    account_age_days: int
    typical_transaction_frequency: int = 5

class TransactionRequest(BaseModel):
    transaction_id: str
    customer: CustomerProfile
    amount: float
    recipient_id: str
    channel: str
    timestamp: datetime

class RiskResponse(BaseModel):
    transaction_id: str
    fraud_score: float
    risk_level: str
    decision: str
    flagged: bool
    risk_factors: List[str]
    action_required: Optional[str] = None

@router.post("/risk-score", response_model=RiskResponse)
async def evaluate_transaction_risk(transaction: TransactionRequest):
    risk_score = 0
    risk_factors = []
    
    amount_ratio = transaction.amount / max(transaction.customer.avg_transaction_amount, 1)
    if amount_ratio > 5:
        risk_score += 25
        risk_factors.append(f"Amount is {amount_ratio:.1f}x higher than typical")
    elif amount_ratio > 3:
        risk_score += 15
        risk_factors.append(f"Amount is {amount_ratio:.1f}x higher than typical")
    
    is_new_recipient = transaction.recipient_id not in transaction.customer.typical_recipients
    if is_new_recipient:
        risk_score += 15
        risk_factors.append(f"New recipient: {transaction.recipient_id}")
        
        if transaction.amount > 10000:
            risk_score += 20
            risk_factors.append(f"Large amount to new recipient")
    
    if transaction.channel == "USSD":
        risk_score += 10
        risk_factors.append(f"Transaction via USSD channel")
    
    if transaction.customer.account_age_days < 30 and transaction.amount > 5000:
        risk_score += 15
        risk_factors.append(f"New account with large transaction")
    
    fraud_score = min(100, risk_score)
    
    if fraud_score >= 70:
        risk_level = "CRITICAL"
        decision = "BLOCKED"
        flagged = True
        action_required = "Customer must visit branch with ID documents"
    elif fraud_score >= 50:
        risk_level = "HIGH"
        decision = "BLOCKED"
        flagged = True
        action_required = "Immediate fraud investigation required"
    elif fraud_score >= 30:
        risk_level = "MEDIUM"
        decision = "STEPPED_UP"
        flagged = False
        action_required = "Additional verification required"
    else:
        risk_level = "LOW"
        decision = "APPROVED"
        flagged = False
        action_required = None
    
    return RiskResponse(
        transaction_id=transaction.transaction_id,
        fraud_score=round(fraud_score, 1),
        risk_level=risk_level,
        decision=decision,
        flagged=flagged,
        risk_factors=risk_factors,
        action_required=action_required
    )

@router.get("/recent")
async def get_recent_transactions(limit: int = 50):
    mock_transactions = []
    for i in range(min(limit, 50)):
        mock_transactions.append({
            "transaction_id": f"TXN_{i:05d}",
            "customer_id": f"USER_{random.randint(0, 99):04d}",
            "amount": random.uniform(100, 5000),
            "recipient": f"RECIPIENT_{random.randint(0, 50)}",
            "channel": random.choice(["USSD", "MOBILE_APP", "BRANCH"]),
            "timestamp": (datetime.now() - timedelta(hours=random.randint(0, 48))).isoformat(),
            "risk_score": random.uniform(0, 100),
            "status": random.choice(["APPROVED", "FLAGGED", "PENDING"])
        })
    return mock_transactions
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime
from app.services.sim_swap_wrapper import query_sim_swap, send_verification_code

router = APIRouter()

class SIMSwapRequest(BaseModel):
    phone_number: str

class SIMSwapResponse(BaseModel):
    phone_number: str
    swapped: bool
    minutes_ago: Optional[int] = None
    hours_ago: Optional[float] = None
    risk_level: str
    source: str
    last_swap_time: Optional[str] = None

class VerificationRequest(BaseModel):
    phone_number: str
    code: Optional[str] = None

class VerificationResponse(BaseModel):
    status: str
    verified: bool = False
    request_id: Optional[str] = None
    message: Optional[str] = None

@router.post("/simswap-check", response_model=SIMSwapResponse)
async def check_sim_swap(request: SIMSwapRequest):
    """
    Check if a SIM card was recently swapped using Vonage API
    Returns SIM swap status and risk level
    """
    result = query_sim_swap(request.phone_number)
    
    return SIMSwapResponse(
        phone_number=result['phone_number'],
        swapped=result['swapped'],
        minutes_ago=result.get('minutes_ago'),
        hours_ago=result.get('hours_ago'),
        risk_level=result.get('risk_level', 'LOW'),
        source=result.get('source', 'unknown'),
        last_swap_time=result.get('last_swap_time')
    )

@router.post("/verify-send")
async def send_verification(request: VerificationRequest):
    """
    Send verification code to phone number via Vonage Verify API
    """
    result = send_verification_code(request.phone_number)
    
    if result.get('error'):
        raise HTTPException(status_code=400, detail=result['error'])
    
    return VerificationResponse(
        status=result.get('status', 'pending'),
        verified=False,
        request_id=result.get('request_id'),
        message=result.get('message', f"Verification code sent to {request.phone_number}")
    )

@router.post("/verify-check")
async def check_verification(request: VerificationRequest):
    """
    Verify the code sent to the phone number
    """
    if not request.code:
        raise HTTPException(status_code=400, detail="Verification code is required")
    
    result = send_verification_code(request.phone_number, request.code)
    
    verified = result.get('verified') or result.get('status') == 'approved'
    
    return VerificationResponse(
        status=result.get('status', 'rejected'),
        verified=verified,
        message="Verification successful" if verified else "Invalid verification code"
    )

@router.get("/simswap-status/{phone_number}")
async def get_sim_status(phone_number: str):
    """
    Get current SIM swap status without creating a new check
    """
    result = query_sim_swap(phone_number)
    
    return {
        "phone_number": phone_number,
        "swapped": result['swapped'],
        "risk_level": result.get('risk_level', 'LOW'),
        "last_check": datetime.now().isoformat(),
        "source": result.get('source', 'unknown')
    }
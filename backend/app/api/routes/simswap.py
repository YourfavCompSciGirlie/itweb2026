from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.sim_swap_wrapper import query_sim_swap

router = APIRouter()

class SIMSwapRequest(BaseModel):
    phone_number: str

class SIMSwapResponse(BaseModel):
    phone_number: str
    swapped: bool
    minutes_ago: Optional[int] = None
    source: str

@router.post("/simswap-check", response_model=SIMSwapResponse)
async def check_sim_swap(request: SIMSwapRequest):
    result = query_sim_swap(request.phone_number)
    return result
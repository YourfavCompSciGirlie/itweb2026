import os
from datetime import datetime, timedelta
import random
import requests
from typing import Dict, Optional

def query_sim_swap(phone_number: str) -> dict:
    """
    Queries Vonage SIM Swap API.
    Falls back to mock data if VONAGE_API_KEY is not set.
    """
    api_key = os.getenv("VONAGE_API_KEY")
    api_secret = os.getenv("VONAGE_API_SECRET")

    if not api_key or not api_secret:
        return _mock_sim_swap(phone_number)

    try:
        # Vonage Number Insight API v2 for SIM swap
        url = "https://api.nexmo.com/ni/v2/ni/async"
        
        response = requests.post(
            url,
            json={
                "phone_number": phone_number,
                "callback": "https://your-callback-url.com/sim-swap-callback"
            },
            auth=(api_key, api_secret)
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "phone_number": phone_number,
                "swapped": data.get('sim_swap', {}).get('status') == 'swapped',
                "minutes_ago": data.get('sim_swap', {}).get('minutes_ago'),
                "source": "vonage",
                "raw_response": data
            }
        else:
            return _mock_sim_swap(phone_number)
            
    except Exception as e:
        print(f"Vonage API error: {e}")
        return _mock_sim_swap(phone_number)


def _mock_sim_swap(phone_number: str) -> dict:
    """
    Returns realistic mock SIM swap data for demo purposes.
    Simulates a 30% chance of recent SIM swap.
    """
    swapped = random.random() < 0.3
    
    if swapped:
        minutes_ago = random.randint(10, 1440)
        hours_ago = round(minutes_ago / 60, 1)
    else:
        minutes_ago = None
        hours_ago = None

    return {
        "phone_number": phone_number,
        "swapped": swapped,
        "minutes_ago": minutes_ago,
        "hours_ago": hours_ago,
        "source": "mock",
        "risk_level": "HIGH" if swapped and hours_ago and hours_ago < 2 else ("MEDIUM" if swapped and hours_ago and hours_ago < 24 else "LOW"),
        "last_swap_time": (datetime.now() - timedelta(minutes=minutes_ago)).isoformat() if swapped and minutes_ago else None
    }


def send_verification_code(phone_number: str, code: Optional[str] = None) -> dict:
    """
    Send verification code via Vonage Verify API
    """
    api_key = os.getenv("VONAGE_API_KEY")
    api_secret = os.getenv("VONAGE_API_SECRET")
    
    if not api_key or not api_secret:
        return _mock_send_verification(phone_number, code)
    
    try:
        if code:
            url = "https://api.nexmo.com/verify/check/json"
            response = requests.post(
                url,
                auth=(api_key, api_secret),
                data={
                    "request_id": os.getenv("LAST_REQUEST_ID", ""),
                    "code": code
                }
            )
            return response.json()
        else:
            url = "https://api.nexmo.com/verify/json"
            response = requests.post(
                url,
                auth=(api_key, api_secret),
                data={
                    "number": phone_number,
                    "brand": "FraudDetectionSystem"
                }
            )
            if response.status_code == 200:
                os.environ["LAST_REQUEST_ID"] = response.json().get("request_id", "")
            return response.json()
            
    except Exception as e:
        print(f"Vonage Verify error: {e}")
        return _mock_send_verification(phone_number, code)


def _mock_send_verification(phone_number: str, code: Optional[str] = None) -> dict:
    """Mock verification for demo"""
    if code:
        if code == "123456":
            return {"status": "approved", "verified": True}
        else:
            return {"status": "rejected", "verified": False, "error": "Invalid code"}
    else:
        return {
            "status": "pending",
            "request_id": f"REQ_{random.randint(10000, 99999)}",
            "message": f"Verification code sent to {phone_number} (mock: use 123456)"
        }
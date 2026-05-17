import os
from datetime import datetime, timedelta
import random

def query_sim_swap(phone_number: str) -> dict:
    """
    Queries Vonage SIM Swap API.
    Falls back to mock data if VONAGE_API_KEY is not set.
    """
    api_key = os.getenv("VONAGE_API_KEY")

    if not api_key:
        # --- MOCK MODE (for development/demo) ---
        return _mock_sim_swap(phone_number)

    # --- REAL VONAGE API (plug in tomorrow) ---
    # TODO: Replace with actual Vonage Number Insight v2 call
    return _mock_sim_swap(phone_number)


def _mock_sim_swap(phone_number: str) -> dict:
    """
    Returns realistic mock SIM swap data for demo purposes.
    Simulates a 30% chance of recent SIM swap.
    """
    swapped = random.random() < 0.3  # 30% chance

    if swapped:
        minutes_ago = random.randint(10, 1400)
    else:
        minutes_ago = None

    return {
        "phone_number": phone_number,
        "swapped": swapped,
        "minutes_ago": minutes_ago,
        "source": "mock"
    }
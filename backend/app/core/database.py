import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_ANON_KEY in .env file")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def log_transaction(
    user_id: str,
    amount: float,
    recipient_phone_hash: str,
    sim_swap_minutes_ago: int,
    risk_score: int,
    decision: str,
    reason: str,
    location_tower: str = None
):
    """Save a transaction result to Supabase."""
    try:
        data = {
            "user_id": user_id,
            "amount": amount,
            "recipient_phone_hash": recipient_phone_hash,
            "sim_swap_minutes_ago": sim_swap_minutes_ago,
            "risk_score": risk_score,
            "decision": decision,
            "reason": reason,
            "location_tower": location_tower
        }
        result = supabase.table("transactions").insert(data).execute()
        return result
    except Exception as e:
        print(f"DB log error: {e}")
        return None


def get_recent_transactions(limit: int = 20):
    """Fetch recent transactions for the dashboard."""
    try:
        result = (
            supabase.table("transactions")
            .select("*")
            .order("timestamp", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data
    except Exception as e:
        print(f"DB fetch error: {e}")
        return []
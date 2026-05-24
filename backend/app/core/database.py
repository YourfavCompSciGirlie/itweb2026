# Mock database module for development
from datetime import datetime
from typing import Dict, List, Optional

def log_transaction(transaction_data: dict) -> dict:
    """
    Mock function to log transactions to database
    In production, this would connect to Supabase or PostgreSQL
    """
    print(f"[MOCK DB] Logging transaction: {transaction_data.get('transaction_id')}")
    
    return {
        "success": True,
        "transaction_id": transaction_data.get('transaction_id'),
        "logged_at": datetime.now().isoformat()
    }

def get_transaction_history(user_id: str, limit: int = 10) -> List[dict]:
    """
    Mock function to get transaction history
    """
    return [
        {
            "transaction_id": f"TXN_{i}",
            "user_id": user_id,
            "amount": 100.0 * i,
            "timestamp": datetime.now().isoformat(),
            "status": "COMPLETED"
        }
        for i in range(limit)
    ]

def update_transaction_status(transaction_id: str, status: str) -> dict:
    """
    Mock function to update transaction status
    """
    return {
        "success": True,
        "transaction_id": transaction_id,
        "status": status,
        "updated_at": datetime.now().isoformat()
    }
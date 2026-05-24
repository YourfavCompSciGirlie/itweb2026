import requests
import json
from datetime import datetime

API_BASE_URL = "http://127.0.0.1:8000"

def check_sim_swap():
    print("\n📱 SIM SWAP CHECK")
    print("-" * 40)
    phone = input("Enter phone number: ")
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/simswap-check", json={"phone_number": phone})
        if response.status_code == 200:
            result = response.json()
            print("\n" + "=" * 40)
            if result['swapped']:
                print(f"🚨 SIM SWAP DETECTED!")
                print(f"   Hours ago: {result['hours_ago']}")
                print(f"   Risk Level: {result['risk_level']}")
            else:
                print(f"✅ No SIM swap detected")
            print(f"   Source: {result['source']}")
            print("=" * 40)
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Connection error: {e}")

def evaluate_transaction():
    print("\n💰 TRANSACTION RISK EVALUATION")
    print("-" * 40)
    
    customer_id = input("Customer ID: ")
    phone = input("Phone number: ")
    amount = float(input("Amount (R): "))
    recipient = input("Recipient ID: ")
    channel = input("Channel (USSD/MOBILE_APP/BRANCH): ").upper()
    
    payload = {
        "transaction_id": f"USSD_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "customer": {
            "customer_id": customer_id,
            "phone_number": phone,
            "avg_transaction_amount": 500,
            "typical_recipients": ["RECIPIENT_001", "RECIPIENT_002"],
            "account_age_days": 365
        },
        "amount": amount,
        "recipient_id": recipient,
        "channel": channel,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/risk-score", json=payload)
        if response.status_code == 200:
            result = response.json()
            print("\n" + "=" * 50)
            print(f"📊 FRAUD SCORE: {result['fraud_score']}/100")
            print(f"📈 RISK LEVEL: {result['risk_level']}")
            print(f"⚖️ DECISION: {result['decision']}")
            
            if result['flagged']:
                print("\n🚨 TRANSACTION FLAGGED!")
            else:
                print("\n✅ Transaction approved")
            
            if result['risk_factors']:
                print("\n⚠️ Risk Factors:")
                for factor in result['risk_factors']:
                    print(f"   • {factor}")
            
            if result['action_required']:
                print(f"\n📋 Action Required: {result['action_required']}")
            
            print("=" * 50)
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Connection error: {e}")

def view_transactions():
    print("\n📋 RECENT TRANSACTIONS")
    print("-" * 40)
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/transactions/recent?limit=10")
        if response.status_code == 200:
            transactions = response.json()
            print(f"\n{'ID':<15} {'Amount':<12} {'Status':<12} {'Risk':<8}")
            print("-" * 55)
            for tx in transactions:
                print(f"{tx['transaction_id']:<15} R{tx['amount']:<10.2f} {tx['status']:<12} {tx.get('risk_score', 'N/A')}")
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Connection error: {e}")

def main():
    print("=" * 50)
    print("🛡️ AEGISAI USSD SIMULATOR")
    print("=" * 50)
    
    while True:
        print("\n📱 MAIN MENU")
        print("1. Check SIM Swap Status")
        print("2. Evaluate Transaction Risk")
        print("3. View Recent Transactions")
        print("4. Exit")
        
        choice = input("\nSelect option (1-4): ")
        
        if choice == "1":
            check_sim_swap()
        elif choice == "2":
            evaluate_transaction()
        elif choice == "3":
            view_transactions()
        elif choice == "4":
            print("\n👋 Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()
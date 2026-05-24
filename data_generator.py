import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from dataclasses import dataclass
from string import Template

@dataclass
class Customer:
    user_id: str
    sim_last_change: datetime
    device_id: str
    is_fraudulent: bool
    kyc_level: str
    account_age_days: int

def generate_fraud_data(n_customers=100):
    np.random.seed(42)
    random.seed(42)
    
    customers = []
    for i in range(n_customers):
        sim_last_changed = datetime.now() - timedelta(days=random.randint(1, 365))
        is_fraud = random.random() < 0.1  

        customer = Customer(
            user_id=f'U{i:04d}',
            sim_last_change=sim_last_changed,
            device_id=f'DEV_{random.randint(1000,9999)}',
            is_fraudulent=is_fraud,
            kyc_level=random.choice(['basic', 'verified', 'premium']),
            account_age_days=random.randint(1, 730)
        )
        customers.append(customer)
    
    df_customers = pd.DataFrame([{
        'user_id': c.user_id,
        'sim_last_change': c.sim_last_change,
        'device_id': c.device_id,
        'is_fraudulent': c.is_fraudulent,
        'kyc_level': c.kyc_level,
        'account_age_days': c.account_age_days
    } for c in customers])
    
    transactions = []
    for i in range(500):
        customer = random.choice(customers)
        txn_time = datetime.now() - timedelta(hours=random.randint(1, 168))
        
        if customer.is_fraudulent:  
            amount = random.uniform(1000, 10000)
            sim_recent = random.random() < 0.7 
        else:
            amount = random.uniform(10, 500)
            sim_recent = False
            
        transactions.append({
            'txn_id': Template('TXN_${id}').substitute(id=f'{i:05d}'),
            'user_id': customer.user_id, 
            'amount': amount,
            'timestamp': txn_time,
            'merchant': random.choice(['FNB', 'Absa', 'Nedbank', 'African Bank', 'Standard Bank']),
            'sim_changed_recently': sim_recent,
            'is_fraud': customer.is_fraudulent 
        })
    
    df_transactions = pd.DataFrame(transactions)
    return df_customers, df_transactions

if __name__ == "__main__":
    customers, transactions = generate_fraud_data(200)
    customers.to_csv('customers.csv', index=False)
    transactions.to_csv('transactions.csv', index=False)
    print("✅ Mock data generated and saved to CSV files!")
    print(f"   - {len(customers)} customers")
    print(f"   - {len(transactions)} transactions")
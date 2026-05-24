import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import json

st.set_page_config(page_title="Fraud Detection System", layout="wide")

API_BASE_URL = "http://127.0.0.1:8000"

if 'transaction_history' not in st.session_state:
    st.session_state.transaction_history = []
if 'risk_results' not in st.session_state:
    st.session_state.risk_results = []

st.title("🕵️ Hybrid Anti-Fraud System")
st.markdown("SIM Swap Verification + Graph Neural Network Detection")
st.markdown(f"**Backend API:** `{API_BASE_URL}`")
st.markdown("---")

@st.cache_data(ttl=5)
def fetch_recent_transactions(limit=50):
    try:
        response = requests.get(f"{API_BASE_URL}/api/transactions/recent", params={"limit": limit}, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch transactions: {response.status_code}")
            return []
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Cannot connect to backend at {API_BASE_URL}. Make sure the backend is running.")
        return []
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []

def evaluate_risk_score(transaction_data):
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/risk-score",
            json=transaction_data,
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Risk evaluation failed: {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Cannot connect to backend at {API_BASE_URL}")
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("System Status", "🟢 Active" if fetch_recent_transactions(1) else "🔴 Offline")
with col2:
    st.metric("API Base URL", API_BASE_URL)
with col3:
    transactions = fetch_recent_transactions(1)
    st.metric("Recent TX", len(transactions) if transactions else 0)
with col4:
    st.metric("Risk Checks", len(st.session_state.risk_results))

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📋 Recent Transactions", "🔍 Test Transaction Risk", "📊 Risk History"])

with tab1:
    st.header("Recent Transactions")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        tx_limit = st.selectbox("Number of transactions", [20, 50, 100, 200], index=1)
        refresh_tx = st.button("🔄 Refresh", type="secondary", use_container_width=True)
    
    with col2:
        if refresh_tx:
            st.cache_data.clear()
    
    transactions_data = fetch_recent_transactions(tx_limit)
    
    if transactions_data:
        transactions_df = pd.DataFrame(transactions_data)
        
        if 'timestamp' in transactions_df.columns:
            transactions_df['timestamp'] = pd.to_datetime(transactions_df['timestamp'])
            transactions_df['date'] = transactions_df['timestamp'].dt.date
        
        st.dataframe(
            transactions_df,
            use_container_width=True,
            column_config={
                "transaction_id": "TX ID",
                "amount": st.column_config.NumberColumn("Amount (R)", format="R %.2f"),
                "risk_score": st.column_config.ProgressColumn("Risk Score", format="%.0f", min_value=0, max_value=100),
                "timestamp": "Time",
                "status": st.column_config.TextColumn("Status")
            }
        )
        
        st.subheader("Transaction Volume")
        if 'amount' in transactions_df.columns:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=transactions_df['transaction_id'].head(20), 
                                 y=transactions_df['amount'].head(20),
                                 marker_color='steelblue'))
            fig.update_layout(title="Recent Transaction Amounts", 
                            xaxis_title="Transaction ID", 
                            yaxis_title="Amount (R)",
                            height=400)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No transactions found or backend not reachable")

with tab2:
    st.header("Test Transaction Risk Score")
    st.markdown("Enter transaction details to get real-time fraud risk assessment")
    
    with st.form("risk_evaluation_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Customer Information")
            customer_id = st.text_input("Customer ID", "CUST001")
            phone_number = st.text_input("Phone Number", "+27821234567")
            account_age_days = st.number_input("Account Age (days)", min_value=1, max_value=3650, value=365)
            avg_transaction_amount = st.number_input("Avg Transaction Amount (R)", min_value=0.0, value=500.0)
            typical_recipients = st.text_input("Typical Recipients (comma separated)", "RECIPIENT_001,RECIPIENT_002")
            typical_recipients_list = [r.strip() for r in typical_recipients.split(",")] if typical_recipients else []
        
        with col2:
            st.subheader("Transaction Details")
            transaction_id = st.text_input("Transaction ID", f"TXN_{datetime.now().strftime('%Y%m%d%H%M%S')}")
            amount = st.number_input("Transaction Amount (R)", min_value=0.0, value=5000.0, step=500.0)
            recipient_id = st.text_input("Recipient ID", "RECIPIENT_NEW")
            channel = st.selectbox("Transaction Channel", ["USSD", "MOBILE_APP", "BRANCH"])
            timestamp = st.datetime_input("Transaction Time", datetime.now())
        
        st.subheader("SIM Swap Information")
        col3, col4 = st.columns(2)
        with col3:
            sim_swap_detected = st.checkbox("SIM Swap Detected")
        with col4:
            hours_since_swap = st.slider("Hours Since SIM Swap", 0, 72, 2, disabled=not sim_swap_detected)
        
        submitted = st.form_submit_button("🚨 EVALUATE RISK", type="primary", use_container_width=True)
        
        if submitted:
            customer_profile = {
                "customer_id": customer_id,
                "phone_number": phone_number,
                "avg_transaction_amount": avg_transaction_amount,
                "typical_recipients": typical_recipients_list,
                "account_age_days": account_age_days,
                "typical_transaction_frequency": 5
            }
            
            transaction_data = {
                "transaction_id": transaction_id,
                "customer": customer_profile,
                "amount": amount,
                "recipient_id": recipient_id,
                "channel": channel,
                "timestamp": timestamp.isoformat(),
                "sim_swap_detected": sim_swap_detected,
                "hours_since_swap": hours_since_swap if sim_swap_detected else None
            }
            
            with st.spinner("Evaluating risk score..."):
                risk_result = evaluate_risk_score(transaction_data)
            
            if risk_result:
                st.session_state.risk_results.insert(0, {
                    "timestamp": datetime.now(),
                    "transaction_id": transaction_id,
                    "customer_id": customer_id,
                    "amount": amount,
                    "risk_score": risk_result.get('fraud_score', 0),
                    "risk_level": risk_result.get('risk_level', 'UNKNOWN'),
                    "decision": risk_result.get('decision', 'UNKNOWN'),
                    "flagged": risk_result.get('flagged', False),
                    "risk_factors": risk_result.get('risk_factors', []),
                    "sim_swap_risk": risk_result.get('sim_swap_risk', False)
                })
                
                st.markdown("---")
                st.subheader("Risk Evaluation Result")
                
                score_color = "red" if risk_result.get('flagged', False) else "green"
                decision_color = "red" if risk_result.get('decision') == "BLOCKED" else ("orange" if risk_result.get('decision') == "STEPPED_UP" else "green")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Fraud Score", f"{risk_result.get('fraud_score', 0)}/100")
                with col2:
                    st.metric("Risk Level", risk_result.get('risk_level', 'UNKNOWN'))
                with col3:
                    st.markdown(f"<h3 style='color: {decision_color};'>{risk_result.get('decision', 'UNKNOWN')}</h3>", unsafe_allow_html=True)
                
                if risk_result.get('flagged', False):
                    st.error("🚨 TRANSACTION FLAGGED FOR FRAUD")
                else:
                    st.success("✅ Transaction passed risk checks")
                
                if risk_result.get('risk_factors'):
                    st.subheader("Risk Factors Identified")
                    for factor in risk_result.get('risk_factors', []):
                        st.write(f"• {factor}")
                
                if risk_result.get('action_required'):
                    st.warning(f"Action Required: {risk_result.get('action_required')}")
                
                st.json(risk_result)

with tab3:
    st.header("Risk Evaluation History")
    
    if st.session_state.risk_results:
        history_df = pd.DataFrame(st.session_state.risk_results)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Evaluations", len(history_df))
        with col2:
            flagged_count = history_df['flagged'].sum() if 'flagged' in history_df.columns else 0
            st.metric("Flagged Transactions", flagged_count)
        with col3:
            avg_score = history_df['risk_score'].mean() if 'risk_score' in history_df.columns else 0
            st.metric("Average Risk Score", f"{avg_score:.1f}")
        with col4:
            high_risk = len(history_df[history_df['risk_score'] >= 65]) if 'risk_score' in history_df.columns else 0
            st.metric("High Risk (≥65)", high_risk)
        
        st.dataframe(
            history_df,
            use_container_width=True,
            column_config={
                "timestamp": "Time",
                "transaction_id": "TX ID",
                "customer_id": "Customer",
                "amount": st.column_config.NumberColumn("Amount", format="R %.2f"),
                "risk_score": st.column_config.ProgressColumn("Risk Score", format="%.0f", min_value=0, max_value=100),
                "decision": st.column_config.TextColumn("Decision"),
                "risk_factors": st.column_config.ListColumn("Risk Factors")
            }
        )
        
        if len(history_df) > 1:
            st.subheader("Risk Score Trend")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=history_df['timestamp'], y=history_df['risk_score'],
                                    mode='lines+markers', name='Risk Score',
                                    line=dict(color='red', width=2),
                                    marker=dict(size=8)))
            fig.add_hline(y=65, line_dash="dash", line_color="red", annotation_text="High Risk Threshold")
            fig.add_hline(y=30, line_dash="dash", line_color="orange", annotation_text="Medium Risk Threshold")
            fig.update_layout(title="Risk Score Over Time", xaxis_title="Time", yaxis_title="Risk Score",
                            height=400, yaxis_range=[0, 100])
            st.plotly_chart(fig, use_container_width=True)
            
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(x=history_df['customer_id'].head(10), y=history_df['risk_score'].head(10),
                                  marker_color='coral'))
            fig2.update_layout(title="Top 10 Risk Scores by Customer", xaxis_title="Customer ID", yaxis_title="Risk Score",
                              height=400, yaxis_range=[0, 100])
            st.plotly_chart(fig2, use_container_width=True)
        
        if st.button("Clear History", type="secondary"):
            st.session_state.risk_results = []
            st.rerun()
    else:
        st.info("No risk evaluations yet. Go to the 'Test Transaction Risk' tab to evaluate transactions.")

st.markdown("---")
st.markdown("### System Information")
st.markdown(f"""
- **Backend API:** `{API_BASE_URL}`
- **Endpoints used:**
  - `GET /api/transactions/recent` - Fetch recent transactions
  - `POST /api/risk-score` - Evaluate transaction risk
- **Risk Scoring:** 0-100 (0=Safe, 100=Fraudulent)
- **Decision thresholds:** 
  - Score ≥65: Blocked/Flagged
  - Score 30-64: Stepped-up verification
  - Score <30: Approved
""")

if st.button("🔄 Refresh All Data"):
    st.cache_data.clear()
    st.rerun()
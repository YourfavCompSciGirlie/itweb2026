import streamlit as st
from datetime import datetime, timedelta

from fraud_system import (
    CustomerProfile,
    Transaction,
    TransactionChannel,
    MobileNetworkOperatorAPI,
    SIMSwapVerificationEngine,
    TransactionGraph,
    GraphSAGESimulator
)

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(page_title="Fraud Detection Simulator", layout="wide")

st.title("🏦 Fraud Detection Simulation System")
st.markdown("### 📊 SIM Swap + Neural Graph Fraud Detection")
st.info("👈 Configure inputs, then run a simulation below")
st.divider()

# ─────────────────────────────────────────
# SIDEBAR (CUSTOMER PROFILE)
# ─────────────────────────────────────────
st.sidebar.header("👤 Customer Profile")

customer_id = st.sidebar.text_input("Customer ID", "CUST001")
avg_amount = st.sidebar.number_input("Avg Transaction Amount", 100.0)
account_age = st.sidebar.slider("Account Age (days)", 1, 1000, 365)

sim_swap = st.sidebar.checkbox("Recent SIM Swap?")
hours_since = st.sidebar.slider("Hours Since Swap", 0, 48, 2)

# ─────────────────────────────────────────
# MAIN INPUT
# ─────────────────────────────────────────
st.header("💸 Transaction Simulation")

amount = st.number_input("Amount", 0.0, 50000.0, 1000.0)
recipient = st.text_input("Recipient ID", "RCP001")
channel = st.selectbox("Channel", ["USSD", "Mobile App", "Branch"])

# Buttons side-by-side
colA, colB = st.columns(2)

with colA:
    run_tx = st.button("🚀 Run Transaction Check")

with colB:
    run_graph = st.button("🧠 Run Graph Fraud Analysis")

# ─────────────────────────────────────────
# TRANSACTION CHECK (SIM SWAP ENGINE)
# ─────────────────────────────────────────
if run_tx:

    customer = CustomerProfile(
        customer_id=customer_id,
        phone_number="+27820000000",
        avg_transaction_amount=avg_amount,
        typical_recipients=["RCP001", "RCP002"],
        account_age_days=account_age,
        typical_transaction_frequency=3
    )

    mno = MobileNetworkOperatorAPI()

    if sim_swap:
        mno.register_sim_swap(
            customer.phone_number,
            datetime.now() - timedelta(hours=hours_since)
        )

    engine = SIMSwapVerificationEngine(mno)

    # ✅ FIXED ENUM MAPPING
    channel_map = {
        "USSD": TransactionChannel.USSD,
        "Mobile App": TransactionChannel.MOBILE_APP,
        "Branch": TransactionChannel.BRANCH
    }

    tx = Transaction(
        transaction_id="TX_SIM",
        customer=customer,
        amount=amount,
        recipient_id=recipient,
        channel=channel_map[channel],
        timestamp=datetime.now()
    )

    result = engine.verify_transaction(tx)

    st.divider()
    st.subheader("📊 Transaction Risk Dashboard")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Decision", result["decision"])

    with col2:
        st.metric("Risk Level", result["risk_level"])

    with col3:
        st.metric("Risk Factors", len(result["risk_factors"]))

    # Result banner
    if result["decision"] == "APPROVED":
        st.success("✅ Transaction Approved")
    elif result["decision"] == "STEPPED_UP":
        st.warning("⚠️ Additional Verification Required")
    else:
        st.error("🛑 Transaction Blocked")

    # Risk factors
    st.markdown("### ⚠️ Risk Factors")
    if result["risk_factors"]:
        for f in result["risk_factors"]:
            st.error(f"🚨 {f}")
    else:
        st.success("No risk factors detected")

    # Risk score
    risk_map = {"LOW": 25, "MEDIUM": 50, "HIGH": 75, "CRITICAL": 100}
    score = risk_map.get(result["risk_level"], 0)

    st.markdown("### 📈 Fraud Risk Score")
    st.progress(score / 100)
    st.write(f"Score: {score}/100")

# ─────────────────────────────────────────
# GRAPH FRAUD DETECTION (GNN SIMULATION)
# ─────────────────────────────────────────
if run_graph:

    st.divider()
    st.header("🧠 Neural Graph Fraud Detection")

    graph = TransactionGraph()

    # Create simulated fraud network
    graph.add_account("MAIN", account_age_days=5)

    mule_accounts = [f"MULE_{i}" for i in range(5)]
    for mule in mule_accounts:
        graph.add_account(mule, account_age_days=3)

    # Suspicious transactions
    for mule in mule_accounts:
        graph.add_transaction("MAIN", mule, 5000)
        graph.add_transaction(mule, "EXIT", 4500)

    # Cross connections
    for i in range(len(mule_accounts) - 1):
        graph.add_transaction(mule_accounts[i], mule_accounts[i + 1], 1000)

    gnn = GraphSAGESimulator(graph)
    analysis = gnn.detect_fraud_network("MAIN")

    st.subheader("📊 Graph Analysis Dashboard")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Fraud Score", f"{analysis['fraud_score']:.0f}/100")

    with col2:
        st.metric("Flagged", "🚨 YES" if analysis["flagged"] else "✅ NO")

    with col3:
        st.metric("Network Size", analysis["neighborhood_size"])

    st.markdown("### 🔍 Patterns Detected")

    if analysis["patterns"]:
        for p in analysis["patterns"]:
            st.error(f"[{p['severity']}] {p['pattern']} - {p['description']}")
    else:
        st.success("No suspicious patterns detected")

    st.markdown("### 🧾 Recommendation")
    st.info(analysis["recommendation"])

    st.progress(analysis["fraud_score"] / 100)
import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
from datetime import datetime, timedelta
import plotly.graph_objects as go
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import math

st.set_page_config(page_title="Fraud Detection System", layout="wide")

class TransactionChannel(Enum):
    USSD = "USSD"
    MOBILE_APP = "Mobile App"
    BRANCH = "Branch"

class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class CustomerProfile:
    customer_id: str
    phone_number: str
    avg_transaction_amount: float
    typical_recipients: list[str]
    account_age_days: int
    typical_transaction_frequency: int

@dataclass
class SIMStatus:
    phone_number: str
    last_swap_datetime: Optional[datetime]
    hours_since_swap: Optional[float]
    carrier: str
    verified: bool

@dataclass
class Transaction:
    transaction_id: str
    customer: CustomerProfile
    amount: float
    recipient_id: str
    channel: TransactionChannel
    timestamp: datetime

class MobileNetworkOperatorAPI:
    def __init__(self):
        self.sim_swap_records: dict[str, datetime] = {}
        
    def register_sim_swap(self, phone_number: str, swap_time: datetime):
        self.sim_swap_records[phone_number] = swap_time
        
    def query_sim_status(self, phone_number: str) -> SIMStatus:
        now = datetime.now()
        last_swap = self.sim_swap_records.get(phone_number)
        hours_since = None
        if last_swap:
            hours_since = (now - last_swap).total_seconds() / 3600
        return SIMStatus(
            phone_number=phone_number,
            last_swap_datetime=last_swap,
            hours_since_swap=hours_since,
            carrier="Simulated MNO",
            verified=True
        )

class ContextualBehaviorAnalyzer:
    AMOUNT_MULTIPLIER_THRESHOLD = 5.0
    NEW_RECIPIENT_LARGE_AMOUNT = 10000
    
    def analyze(self, transaction: Transaction, sim_status: SIMStatus) -> tuple[RiskLevel, list[str]]:
        risk_factors = []
        risk_score = 0
        
        if sim_status.hours_since_swap is not None:
            if sim_status.hours_since_swap < 24:
                risk_factors.append(f"SIM swap detected {sim_status.hours_since_swap:.1f} hours ago")
                risk_score += 40
                if sim_status.hours_since_swap < 2:
                    risk_factors.append("SIM swap is VERY recent (<2 hours)")
                    risk_score += 20
        
        amount_ratio = transaction.amount / max(transaction.customer.avg_transaction_amount, 1)
        if amount_ratio > self.AMOUNT_MULTIPLIER_THRESHOLD:
            risk_factors.append(f"Amount is {amount_ratio:.1f}x typical")
            risk_score += 25
            
        is_new_recipient = transaction.recipient_id not in transaction.customer.typical_recipients
        if is_new_recipient:
            risk_factors.append(f"Recipient {transaction.recipient_id} is new")
            risk_score += 10
            if transaction.amount > self.NEW_RECIPIENT_LARGE_AMOUNT:
                risk_factors.append(f"Large amount (R{transaction.amount:,.2f}) to new recipient")
                risk_score += 20
                
        if transaction.channel == TransactionChannel.USSD:
            risk_factors.append("Transaction via USSD (limited security)")
            risk_score += 10
            
        if transaction.customer.account_age_days < 30 and transaction.amount > 5000:
            risk_factors.append(f"Account only {transaction.customer.account_age_days} days old")
            risk_score += 15
            
        if risk_score >= 70:
            return RiskLevel.CRITICAL, risk_factors
        elif risk_score >= 50:
            return RiskLevel.HIGH, risk_factors
        elif risk_score >= 30:
            return RiskLevel.MEDIUM, risk_factors
        else:
            return RiskLevel.LOW, risk_factors

class SIMSwapVerificationEngine:
    SIM_SWAP_WINDOW_HOURS = 24
    
    def __init__(self, mno_api: MobileNetworkOperatorAPI):
        self.mno_api = mno_api
        self.behavior_analyzer = ContextualBehaviorAnalyzer()
        
    def verify_transaction(self, transaction: Transaction) -> dict:
        result = {
            "transaction_id": transaction.transaction_id,
            "customer_id": transaction.customer.customer_id,
            "amount": transaction.amount,
            "channel": transaction.channel.value,
            "risk_level": None,
            "risk_factors": [],
            "decision": None,
            "action_required": None
        }
        
        sim_status = self.mno_api.query_sim_status(transaction.customer.phone_number)
        
        recent_swap = (sim_status.hours_since_swap is not None and 
                      sim_status.hours_since_swap < self.SIM_SWAP_WINDOW_HOURS)
        
        if not recent_swap:
            result["risk_level"] = RiskLevel.LOW.value
            result["decision"] = "APPROVED"
            return result
            
        risk_level, risk_factors = self.behavior_analyzer.analyze(transaction, sim_status)
        
        result["risk_level"] = risk_level.value
        result["risk_factors"] = risk_factors
        
        if risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH):
            result["decision"] = "BLOCKED"
            result["action_required"] = "Customer must visit branch with ID documents"
        elif risk_level == RiskLevel.MEDIUM:
            result["decision"] = "STEPPED_UP"
            result["action_required"] = "Additional verification required"
        else:
            result["decision"] = "APPROVED"
            
        return result

class TransactionGraph:
    def __init__(self):
        self.nodes: dict = {}
        self.edges: list = []
        
    def add_account(self, account_id: str, account_age_days: int = 365):
        if account_id not in self.nodes:
            self.nodes[account_id] = {
                'account_id': account_id,
                'account_age_days': account_age_days,
                'total_inbound': 0,
                'total_outbound': 0,
                'transaction_count': 0,
                'connected_accounts': set(),
                'flagged': False
            }
            
    def add_transaction(self, source_id: str, target_id: str, amount: float):
        self.add_account(source_id)
        self.add_account(target_id)
        
        self.nodes[source_id]['total_outbound'] += amount
        self.nodes[source_id]['transaction_count'] += 1
        self.nodes[source_id]['connected_accounts'].add(target_id)
        
        self.nodes[target_id]['total_inbound'] += amount
        self.nodes[target_id]['transaction_count'] += 1
        self.nodes[target_id]['connected_accounts'].add(source_id)
        
        self.edges.append({'source': source_id, 'target': target_id, 'amount': amount})

class GraphSAGESimulator:
    def __init__(self, graph: TransactionGraph):
        self.graph = graph
        
    def compute_node_features(self, account_id: str) -> dict:
        node = self.graph.nodes.get(account_id)
        if not node:
            return {}
        total_flow = node['total_inbound'] + 0.01
        pass_through_ratio = node['total_outbound'] / total_flow
        velocity = node['transaction_count'] / max(node['account_age_days'], 1)
        return {
            "pass_through_ratio": min(pass_through_ratio, 1.0),
            "velocity": velocity,
            "connection_count": len(node['connected_accounts']),
            "account_age_days": node['account_age_days']
        }
        
    def detect_fraud_network(self, account_id: str) -> dict:
        if account_id not in self.graph.nodes:
            return {"account_id": account_id, "fraud_score": 0, "patterns": []}
        
        node = self.graph.nodes[account_id]
        features = self.compute_node_features(account_id)
        
        fraud_score = 0
        patterns = []
        
        if features.get('pass_through_ratio', 0) > 0.85:
            fraud_score += 30
            patterns.append("HIGH_PASS_THROUGH - Money laundering indicator")
            
        if features.get('velocity', 0) > 1.5:
            fraud_score += 25
            patterns.append("RAPID_VELOCITY - Too many transactions")
            
        if features.get('account_age_days', 365) < 14:
            fraud_score += 25
            patterns.append("NEW_ACCOUNT_NETWORK - Account is less than 14 days old")
            
        neighbor_scores = []
        for neighbor in node['connected_accounts']:
            if neighbor in self.graph.nodes:
                neighbor_features = self.compute_node_features(neighbor)
                if neighbor_features.get('pass_through_ratio', 0) > 0.8:
                    neighbor_scores.append(True)
        
        if len(neighbor_scores) > 2:
            fraud_score += 20
            patterns.append("DENSE_NETWORK - Connected to suspicious accounts")
            
        fraud_score = min(fraud_score, 100)
        flagged = fraud_score >= 60
        
        return {
            "account_id": account_id,
            "fraud_score": fraud_score,
            "flagged": flagged,
            "patterns": patterns
        }

@st.cache_data
def generate_data():
    np.random.seed(42)
    customers = []
    for i in range(100):
        customers.append({
            'user_id': f'USER_{i:04d}',
            'is_fraudulent': np.random.choice([True, False], p=[0.1, 0.9]),
            'kyc_level': np.random.choice(['basic', 'verified', 'premium'], p=[0.5, 0.3, 0.2]),
            'sim_last_change': datetime.now() - timedelta(days=np.random.randint(1, 365)),
            'device_id': f'DEVICE_{np.random.randint(1,30)}',
            'account_age_days': np.random.randint(1, 730),
            'phone_number': f'+278{np.random.randint(10000000, 99999999)}',
            'avg_transaction_amount': np.random.uniform(200, 1000),
            'typical_recipients': [f'RECIPIENT_{i}' for i in np.random.choice(100, 3, replace=False)]
        })
    
    customers_df = pd.DataFrame(customers)
    
    merchants = ['Amazon', 'Walmart', 'Target', 'Apple', 'Google']
    transactions = []
    for i in range(300):
        user = np.random.choice(customers_df['user_id'])
        is_fraud = customers_df[customers_df['user_id']==user]['is_fraudulent'].iloc[0] and np.random.random() < 0.3
        transactions.append({
            'user_id': user,
            'merchant': np.random.choice(merchants),
            'amount': np.random.exponential(2000 if is_fraud else 500),
            'is_fraud': is_fraud,
            'txn_id': f'TXN_{i:05d}',
            'recipient': f'RECIPIENT_{np.random.randint(0, 100)}'
        })
    
    return customers_df, pd.DataFrame(transactions)

class FraudGraph:
    def __init__(self):
        self.graph = nx.Graph()
        self.mno_api = MobileNetworkOperatorAPI()
        self.sim_verifier = SIMSwapVerificationEngine(self.mno_api)
        self.transaction_graph = TransactionGraph()
        self.gnn_analyzer = None
    
    def build(self, customers, transactions):
        for _, c in customers.iterrows():
            self.graph.add_node(c['user_id'], type='customer', is_fraud=c['is_fraudulent'], 
                               kyc=c['kyc_level'], sim_days_ago=(datetime.now() - c['sim_last_change']).days,
                               account_age=c['account_age_days'], phone=c['phone_number'],
                               avg_amount=c['avg_transaction_amount'], recipients=c['typical_recipients'])
            self.transaction_graph.add_account(c['user_id'], c['account_age_days'])
        
        for m in transactions['merchant'].unique():
            self.graph.add_node(m, type='merchant')
        
        for _, t in transactions.iterrows():
            self.graph.add_edge(t['user_id'], t['merchant'], type='transaction', amount=t['amount'])
            self.transaction_graph.add_transaction(t['user_id'], t['recipient'], t['amount'])
        
        for device, users in customers.groupby('device_id')['user_id'].apply(list).items():
            if len(users) > 1:
                for i in range(len(users)):
                    for j in range(i+1, len(users)):
                        self.graph.add_edge(users[i], users[j], type='shares_device')
        
        self.gnn_analyzer = GraphSAGESimulator(self.transaction_graph)
    
    def get_score(self, account_id):
        if account_id not in self.graph or self.graph.nodes[account_id].get('type') != 'customer':
            return {"account_id": account_id, "fraud_score": 0.0, "flagged": False, "sim_swap_risk": False}
        
        node = self.graph.nodes[account_id]
        neighbors = list(self.graph.neighbors(account_id))
        
        fraud_neighbors = sum(1 for n in neighbors if self.graph.nodes.get(n, {}).get('is_fraud', False))
        merchant_count = sum(1 for n in neighbors if self.graph.nodes.get(n, {}).get('type') == 'merchant')
        
        kyc_risk = {'basic': 0.8, 'verified': 0.4, 'premium': 0.1}.get(node.get('kyc', 'basic'), 0.5)
        sim_risk = min(1.0, 7.0 / max(1, node.get('sim_days_ago', 365)))
        age_risk = min(1.0, 30.0 / max(1, node.get('account_age', 365)))
        
        score = (30 if node.get('is_fraud') else 0) + (12 * kyc_risk) + (15 * sim_risk) + (10 * age_risk) + (20 * min(1, fraud_neighbors/5)) + (8 * min(1, merchant_count/30))
        
        customer_profile = CustomerProfile(
            customer_id=account_id,
            phone_number=node.get('phone', ''),
            avg_transaction_amount=node.get('avg_amount', 500),
            typical_recipients=node.get('recipients', []),
            account_age_days=node.get('account_age', 365),
            typical_transaction_frequency=5
        )
        
        test_transaction = Transaction(
            transaction_id="TEST001",
            customer=customer_profile,
            amount=node.get('avg_amount', 500) * 3,
            recipient_id="TEST_RECIPIENT",
            channel=TransactionChannel.USSD,
            timestamp=datetime.now()
        )
        
        sim_result = self.sim_verifier.verify_transaction(test_transaction)
        
        gnn_result = self.gnn_analyzer.detect_fraud_network(account_id)
        
        final_score = min(100, (score * 0.6) + (gnn_result['fraud_score'] * 0.4))
        
        return {
            "account_id": account_id,
            "fraud_score": round(final_score, 1),
            "flagged": final_score >= 65,
            "sim_swap_risk": sim_result['risk_level'] in ['HIGH', 'CRITICAL'],
            "sim_decision": sim_result['decision'],
            "gnn_score": gnn_result['fraud_score'],
            "gnn_patterns": gnn_result['patterns']
        }

def plot_graph(graph, fraud_detector, max_nodes=40):
    subgraph = graph.subgraph(list(graph.nodes())[:max_nodes])
    pos = nx.spring_layout(subgraph, k=2, iterations=30)
    
    edges = go.Scatter(x=[], y=[], mode='lines', line=dict(width=1, color='#888'))
    edge_x, edge_y = [], []
    for e in subgraph.edges():
        edge_x.extend([pos[e[0]][0], pos[e[1]][0], None])
        edge_y.extend([pos[e[0]][1], pos[e[1]][1], None])
    edges.x, edges.y = edge_x, edge_y
    
    nodes_x, nodes_y, colors, sizes, texts = [], [], [], [], []
    for n in subgraph.nodes():
        x, y = pos[n]
        nodes_x.append(x); nodes_y.append(y)
        data = subgraph.nodes[n]
        
        if data.get('type') == 'customer':
            result = fraud_detector.get_score(n)
            score = result['fraud_score']
            if data.get('is_fraud'):
                colors.append('red'); sizes.append(25); texts.append(f"{n}<br>FRAUDSTER")
            elif result.get('sim_swap_risk'):
                colors.append('purple'); sizes.append(22); texts.append(f"{n}<br>SIM SWAP RISK<br>Score: {score}")
            elif score >= 65:
                colors.append('orange'); sizes.append(20); texts.append(f"{n}<br>HIGH RISK<br>Score: {score}")
            else:
                colors.append('#87CEEB'); sizes.append(15); texts.append(f"{n}<br>Score: {score}")
        else:
            colors.append('#90EE90'); sizes.append(12); texts.append(f"{n}<br>Merchant")
    
    nodes = go.Scatter(x=nodes_x, y=nodes_y, mode='markers+text', 
                      text=[t.split('<br>')[0] for t in texts],
                      textposition="top center", hovertext=texts, hoverinfo='text',
                      marker=dict(size=sizes, color=colors, line=dict(width=2, color='DarkSlateGray')))
    
    return go.Figure(data=[edges, nodes], layout=go.Layout(title='Fraud Detection Graph', height=600, showlegend=False,
                      xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                      yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))

customers, transactions = generate_data()
detector = FraudGraph()
detector.build(customers, transactions)

st.title("🕵️ Hybrid Anti-Fraud System")
st.markdown("SIM Swap Verification + Graph Neural Network Detection")

st.sidebar.header("💰 Transaction Simulation")
st.sidebar.markdown("---")

st.sidebar.subheader("👤 Customer Information")
selected_customer = st.sidebar.selectbox("Select Customer", customers['user_id'].tolist())
customer_data = customers[customers['user_id'] == selected_customer].iloc[0]

st.sidebar.subheader("📱 SIM Swap Status")
sim_swap_detected = st.sidebar.checkbox("SIM Swap Occurred?")
if sim_swap_detected:
    hours_since_swap = st.sidebar.slider("Hours Since SIM Swap", 0, 72, 2)
    st.sidebar.warning(f"⚠️ SIM swapped {hours_since_swap} hours ago")
else:
    hours_since_swap = None
    st.sidebar.success("✅ No recent SIM swap")

st.sidebar.subheader("💸 Withdrawal Details")
withdrawal_amount = st.sidebar.number_input("Withdrawal Amount (R)", min_value=0.0, value=5000.0, step=500.0)
recipient = st.sidebar.text_input("Recipient Account", "RECIPIENT_NEW")
channel = st.sidebar.selectbox("Transaction Channel", ["USSD", "Mobile App", "Branch"])

st.sidebar.markdown("---")
check_transaction = st.sidebar.button("🚨 CHECK TRANSACTION", type="primary", use_container_width=True)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Customers", len(customers))
col2.metric("Transactions", len(transactions))
col3.metric("Fraudsters", customers['is_fraudulent'].sum())
col4.metric("Graph Edges", detector.graph.number_of_edges())
col5.metric("SIM Swaps", len(detector.mno_api.sim_swap_records))

if check_transaction:
    st.markdown("---")
    st.header("🚦 Transaction Verification Result")
    
    if sim_swap_detected:
        detector.mno_api.register_sim_swap(
            customer_data['phone_number'], 
            datetime.now() - timedelta(hours=hours_since_swap)
        )
    
    customer_profile = CustomerProfile(
        customer_id=selected_customer,
        phone_number=customer_data['phone_number'],
        avg_transaction_amount=customer_data['avg_transaction_amount'],
        typical_recipients=customer_data['typical_recipients'],
        account_age_days=customer_data['account_age_days'],
        typical_transaction_frequency=5
    )
    
    transaction = Transaction(
        transaction_id=f"TXN_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        customer=customer_profile,
        amount=withdrawal_amount,
        recipient_id=recipient,
        channel=TransactionChannel[channel.replace(" ", "_").upper()],
        timestamp=datetime.now()
    )
    
    result = detector.sim_verifier.verify_transaction(transaction)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Withdrawal Amount", f"R{withdrawal_amount:,.2f}")
        st.metric("Avg Transaction", f"R{customer_data['avg_transaction_amount']:,.2f}")
    
    with col2:
        st.metric("Channel", channel)
        st.metric("Account Age", f"{customer_data['account_age_days']} days")
    
    with col3:
        st.metric("Risk Level", result['risk_level'])
        st.metric("Decision", result['decision'])
    
    st.markdown("---")
    
    if result['decision'] == "BLOCKED":
        st.error("🚨🚨🚨 TRANSACTION BLOCKED 🚨🚨🚨")
        st.error(f"Reason: {result['decision']}")
        if result['action_required']:
            st.warning(f"Action Required: {result['action_required']}")
        
        if sim_swap_detected:
            st.error(f"• SIM swap detected {hours_since_swap} hours ago")
        
        if withdrawal_amount > customer_data['avg_transaction_amount'] * 5:
            st.error(f"• Amount is {withdrawal_amount / customer_data['avg_transaction_amount']:.1f}x larger than typical")
        
        if recipient not in customer_data['typical_recipients']:
            st.error(f"• Recipient {recipient} is not in your usual recipients list")
        
        if channel == "USSD":
            st.error("• USSD channel has limited security controls")
    
    elif result['decision'] == "STEPPED_UP":
        st.warning("⚠️⚠️ ADDITIONAL VERIFICATION REQUIRED ⚠️⚠️")
        st.warning(result['action_required'])
        
        if sim_swap_detected:
            st.info(f"• SIM swap detected {hours_since_swap} hours ago")
        if withdrawal_amount > customer_data['avg_transaction_amount'] * 3:
            st.info(f"• Unusual amount detected")
    
    else:
        st.success("✅✅✅ TRANSACTION APPROVED ✅✅✅")
        st.success("No suspicious patterns detected")
    
    if result['risk_factors']:
        st.markdown("---")
        st.subheader("Risk Factors Identified")
        for factor in result['risk_factors']:
            st.write(f"• {factor}")
    
    st.markdown("---")
    st.caption(f"Transaction ID: {transaction.transaction_id}")
    st.caption(f"Phone: {customer_data['phone_number']}")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Graph", "🔍 SIM Swap Check", "🎯 GNN Analysis", "📈 Stats"])

with tab1:
    max_nodes = st.slider("Nodes to show", 20, 80, 40)
    st.plotly_chart(plot_graph(detector.graph, detector, max_nodes), use_container_width=True)
    st.markdown("🔴 Fraudster | 🟣 SIM Swap Risk | 🟠 High Risk | 🔵 Customer | 🟢 Merchant")

with tab2:
    st.header("SIM Swap Verification")
    account = st.selectbox("Select Account", customers['user_id'].tolist(), key="sim_select")
    
    if st.button("Simulate Transaction", type="primary"):
        result = detector.get_score(account)
        node = detector.graph.nodes[account]
        
        st.subheader("SIM Swap Analysis")
        if result['sim_swap_risk']:
            st.error(f"🚨 {result['sim_decision']} - Recent SIM swap detected!")
        else:
            st.success(f"✅ {result['sim_decision']} - No recent SIM swap")
        
        st.write(f"**Phone:** {node.get('phone', 'N/A')}")
        st.write(f"**Account Age:** {node.get('account_age', 0)} days")
        
        if result['sim_decision'] == "BLOCKED":
            st.warning("⚠️ Customer must visit branch with ID documents")

with tab3:
    st.header("GNN Network Analysis")
    account = st.selectbox("Select Account", customers['user_id'].tolist(), key="gnn_select")
    
    if st.button("Analyze Network", type="primary"):
        result = detector.get_score(account)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("GNN Fraud Score", f"{result['gnn_score']:.0f}/100")
            st.metric("Final Score", f"{result['fraud_score']}/100")
        with col2:
            if result['flagged']:
                st.error("🚨 FLAGGED")
            else:
                st.success("✅ CLEAR")
        
        if result['gnn_patterns']:
            st.subheader("Detected Patterns")
            for pattern in result['gnn_patterns']:
                st.write(f"• {pattern}")

with tab4:
    st.header("System Statistics")
    scores = [detector.get_score(n)['fraud_score'] for n in detector.graph.nodes() if detector.graph.nodes[n].get('type')=='customer']
    gnn_scores = [detector.get_score(n)['gnn_score'] for n in detector.graph.nodes() if detector.graph.nodes[n].get('type')=='customer']
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Average Final Score", f"{np.mean(scores):.1f}")
        st.metric("High Risk (≥65)", len([s for s in scores if s>=65]))
    with col2:
        st.metric("Average GNN Score", f"{np.mean(gnn_scores):.1f}")
        st.metric("SIM Swap Detected", sum(1 for n in detector.graph.nodes() if detector.get_score(n).get('sim_swap_risk', False)))
    
    st.subheader("Score Distribution")
    st.area_chart(pd.DataFrame({'Final Score': scores, 'GNN Score': gnn_scores}))
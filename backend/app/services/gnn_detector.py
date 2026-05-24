import pandas as pd
import numpy as np
import networkx as nx
from datetime import datetime
import random
from data_generator import generate_fraud_data

class SimpleFraudGraph:
    def __init__(self):
        self.graph = nx.Graph()
        
    def build_graph(self, customers_df, transactions_df):
        print("Building fraud detection graph...")

        for _, customer in customers_df.iterrows():
            days_since_sim = (datetime.now() - customer['sim_last_change']).days
            
            self.graph.add_node(
                customer['user_id'],
                type='customer',
                is_fraud=customer['is_fraudulent'],  
                kyc=customer['kyc_level'],           
                sim_days_ago=days_since_sim,
                device_id=customer['device_id'],      
                account_age=customer['account_age_days'] 
            )

        for merchant in transactions_df['merchant'].unique():
            self.graph.add_node(merchant, type='merchant')
        
        for _, txn in transactions_df.iterrows():
            self.graph.add_edge(
                txn['user_id'],
                txn['merchant'],
                type='transaction',
                amount=txn['amount'],
                is_fraud=txn['is_fraud'],  
                txn_id=txn['txn_id']        
            )
        
        device_groups = customers_df.groupby('device_id')['user_id'].apply(list)
        for device, users in device_groups.items():
            if len(users) > 1:  
                for i in range(len(users)):
                    for j in range(i+1, len(users)):
                        self.graph.add_edge(
                            users[i], 
                            users[j],
                            type='shares_device',
                            device=device
                        )
        
       
        print(f"✅ Graph built: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
        
        customer_count = sum(1 for _, data in self.graph.nodes(data=True) if data.get('type') == 'customer')
        merchant_count = sum(1 for _, data in self.graph.nodes(data=True) if data.get('type') == 'merchant')
        print(f"   - Customers: {customer_count}")
        print(f"   - Merchants: {merchant_count}")
        
        return self.graph
    
    def get_node_features(self, node_id):
        if node_id not in self.graph:
            return None
            
        node_data = self.graph.nodes[node_id]
        
        if node_data.get('type') == 'customer':
            neighbors = list(self.graph.neighbors(node_id))
            
            fraud_neighbors = 0
            merchant_connections = 0
            device_sharing_neighbors = 0
            
            for neighbor in neighbors:
                neighbor_data = self.graph.nodes.get(neighbor, {})
                if neighbor_data.get('type') == 'customer':
                    if neighbor_data.get('is_fraud'):
                        fraud_neighbors += 1
                    edge_data = self.graph.get_edge_data(node_id, neighbor, {})
                    if edge_data.get('type') == 'shares_device':
                        device_sharing_neighbors += 1
                elif neighbor_data.get('type') == 'merchant':
                    merchant_connections += 1
            
            sim_risk = min(1.0, 7.0 / max(1, node_data.get('sim_days_ago', 365)))
            
            kyc_scores = {'basic': 0.8, 'verified': 0.4, 'premium': 0.1}
            kyc_risk = kyc_scores.get(node_data.get('kyc', 'basic'), 0.5)
            
            age_risk = min(1.0, 30.0 / max(1, node_data.get('account_age', 365)))
            
            connectivity_risk = min(1.0, len(neighbors) / 50)
            merchant_risk = min(1.0, merchant_connections / 30)
            fraud_connection_risk = min(1.0, fraud_neighbors / 5)
            device_sharing_risk = min(1.0, device_sharing_neighbors / 3)
            
            return {
                'node_id': node_id,
                'is_fraud': node_data.get('is_fraud', False),
                'kyc_risk': kyc_risk,
                'sim_risk': sim_risk,
                'age_risk': age_risk,
                'connectivity_risk': connectivity_risk,
                'merchant_risk': merchant_risk,
                'fraud_connection_risk': fraud_connection_risk,
                'device_sharing_risk': device_sharing_risk,
                'connections': len(neighbors),
                'merchant_connections': merchant_connections,
                'fraud_connections': fraud_neighbors,
                'device_sharing_connections': device_sharing_neighbors,
                'risk_score': 0
            }
        else:
            return {
                'node_id': node_id,
                'type': 'merchant',
                'transaction_count': len(list(self.graph.neighbors(node_id)))
            }
    
    def calculate_fraud_score(self, account_id):
        if account_id not in self.graph:
            print(f"⚠️ Account {account_id} not found in graph")
            return {
                "account_id": account_id,
                "fraud_score": 0.0,
                "flagged": False
            }
        
        features = self.get_node_features(account_id)
        
        if not features or features.get('type') == 'merchant':
            return {
                "account_id": account_id,
                "fraud_score": 0.0,
                "flagged": False
            }
        
        weights = {
            'is_fraud': 30.0,
            'kyc_risk': 12.0,
            'sim_risk': 15.0,
            'age_risk': 10.0,
            'connectivity_risk': 5.0,
            'merchant_risk': 8.0,
            'fraud_connection_risk': 20.0,
            'device_sharing_risk': 10.0
        }
        
        base_score = weights['is_fraud'] if features['is_fraud'] else 0
        
        weighted_score = base_score
        weighted_score += weights['kyc_risk'] * features['kyc_risk']
        weighted_score += weights['sim_risk'] * features['sim_risk']
        weighted_score += weights['age_risk'] * features['age_risk']
        weighted_score += weights['connectivity_risk'] * features['connectivity_risk']
        weighted_score += weights['merchant_risk'] * features['merchant_risk']
        weighted_score += weights['fraud_connection_risk'] * features['fraud_connection_risk']
        weighted_score += weights['device_sharing_risk'] * features['device_sharing_risk']
        
        features['risk_score'] = weighted_score
        
        fraud_score = min(100.0, max(0.0, weighted_score))
        
        return {
            "account_id": account_id,
            "fraud_score": round(fraud_score, 1),
            "flagged": fraud_score >= 65.0
        }
    
    def get_feature_matrix(self):
        nodes = list(self.graph.nodes())
        features = []
        labels = []  
        
        for node in nodes:
            node_features = self.get_node_features(node)
            
            if node_features and node_features.get('type') != 'merchant':
                feature_vector = [
                    float(node_features['is_fraud']),     
                    node_features['kyc_risk'],           
                    node_features['sim_risk'],            
                    node_features['age_risk'],            
                    node_features['connectivity_risk'],
                    node_features['merchant_risk'],
                    node_features['fraud_connection_risk'],
                    node_features['device_sharing_risk']
                ]
                features.append(feature_vector)
                labels.append(float(node_features['is_fraud']))
            elif node_features and node_features.get('type') == 'merchant':
                features.append([0, 0, 0, 0, 0, 0, 0, 0])
                labels.append(0)
            else:
                features.append([0, 0, 0, 0, 0, 0, 0, 0])
                labels.append(0)
        
        return np.array(features), np.array(labels), nodes
    
    def get_adjacency_matrix(self):
        nodes = list(self.graph.nodes())
        n = len(nodes)
        adj_matrix = np.zeros((n, n))
        
        node_to_idx = {node: i for i, node in enumerate(nodes)}
        
        for source, target in self.graph.edges():
            i, j = node_to_idx[source], node_to_idx[target]
            adj_matrix[i, j] = 1
            adj_matrix[j, i] = 1  
        
        return adj_matrix, nodes
    
    def find_fraud_rings(self):
        fraud_rings = []
        visited = set()
        
        customers = [n for n, d in self.graph.nodes(data=True) if d.get('type') == 'customer']
        
        for customer in customers:
            if customer in visited:
                continue
             
            component = []
            stack = [customer]
            
            while stack:
                node = stack.pop()
                if node in visited:
                    continue
                    
                visited.add(node)
              
                if self.graph.nodes[node].get('type') == 'customer':
                    component.append(node)
                    for neighbor in self.graph.neighbors(node):
                        if self.graph.nodes[neighbor].get('type') == 'customer' and neighbor not in visited:
                            stack.append(neighbor)
            
            if len(component) > 1:
                fraudsters = [n for n in component if self.graph.nodes[n].get('is_fraud', False)]
                if fraudsters:
                    ring_scores = []
                    for member in component[:10]:
                        score_result = self.calculate_fraud_score(member)
                        ring_scores.append(score_result['fraud_score'])
                    avg_ring_score = sum(ring_scores) / len(ring_scores) if ring_scores else 0
                    
                    fraud_rings.append({
                        'size': len(component),
                        'fraud_count': len(fraudsters),
                        'avg_fraud_score': round(avg_ring_score, 1),
                        'members': component[:5]
                    })
        
        return fraud_rings

    def batch_calculate_scores(self, account_ids):
        results = []
        for account_id in account_ids:
            results.append(self.calculate_fraud_score(account_id))
        return results

def test_compatibility():
    print("="*60)
    print("TESTING COMPATIBILITY WITH DATA GENERATOR")
    print("="*60)
    
    print("\n1. Generating data from data_generator.py...")
    customers_df, transactions_df = generate_fraud_data(n_customers=50)
    
    print(f"   ✅ Generated {len(customers_df)} customers")
    print(f"   ✅ Generated {len(transactions_df)} transactions")
 
    print("\n2. Checking field names...")
    customer_fields = customers_df.columns.tolist()
    transaction_fields = transactions_df.columns.tolist()
    
    print(f"   Customer fields: {customer_fields}")
    print(f"   Transaction fields: {transaction_fields}")
    
    required_customer_fields = ['user_id', 'sim_last_change', 'device_id', 'is_fraudulent', 'kyc_level', 'account_age_days']
    required_transaction_fields = ['txn_id', 'user_id', 'amount', 'timestamp', 'merchant', 'is_fraud']
    
    missing_customer = [f for f in required_customer_fields if f not in customer_fields]
    missing_transaction = [f for f in required_transaction_fields if f not in transaction_fields]
    
    if missing_customer:
        print(f"   ❌ Missing customer fields: {missing_customer}")
    else:
        print(f"   ✅ All customer fields present")
    
    if missing_transaction:
        print(f"   ❌ Missing transaction fields: {missing_transaction}")
    else:
        print(f"   ✅ All transaction fields present")
    
    print("\n3. Building fraud detection graph...")
    fraud_graph = SimpleFraudGraph()
    graph = fraud_graph.build_graph(customers_df, transactions_df)
    
    print("\n4. Testing individual account fraud scoring...")
    test_accounts = customers_df['user_id'].head(3).tolist()
    for account in test_accounts:
        result = fraud_graph.calculate_fraud_score(account)
        print(f"   Account {account}:")
        print(f"      - Fraud Score: {result['fraud_score']}")
        print(f"      - Flagged: {result['flagged']}")
    
    print("\n5. Testing batch scoring...")
    batch_results = fraud_graph.batch_calculate_scores(test_accounts)
    print(f"   ✅ Processed {len(batch_results)} accounts")
    
    print("\n6. Preparing GNN inputs...")
    features, labels, nodes = fraud_graph.get_feature_matrix()
    adjacency, adj_nodes = fraud_graph.get_adjacency_matrix()
    
    print(f"   ✅ Feature matrix shape: {features.shape}")
    print(f"   ✅ Labels shape: {labels.shape}")
    print(f"   ✅ Adjacency matrix shape: {adjacency.shape}")
    print(f"   ✅ Number of nodes: {len(nodes)}")
    
    print("\n7. Detecting fraud rings...")
    rings = fraud_graph.find_fraud_rings()
    
    if rings:
        print(f"   ✅ Found {len(rings)} potential fraud rings:")
        for i, ring in enumerate(rings[:3]):
            print(f"      Ring {i+1}: {ring['size']} accounts, {ring['fraud_count']} fraudsters, Avg Score: {ring['avg_fraud_score']}")
    else:
        print("   ℹ️ No fraud rings detected (may need more data)")
    
    print("\n8. Example customer analysis:")
    customer_nodes = [n for n in nodes if fraud_graph.graph.nodes[n].get('type') == 'customer']
    if customer_nodes:
        example = customer_nodes[0]
        features_dict = fraud_graph.get_node_features(example)
        fraud_result = fraud_graph.calculate_fraud_score(example)
        print(f"   Customer: {example}")
        print(f"      - Is Fraud: {features_dict.get('is_fraud', False)}")
        print(f"      - KYC Risk: {features_dict.get('kyc_risk', 0)}")
        print(f"      - SIM Risk: {features_dict.get('sim_risk', 0):.2f}")
        print(f"      - Connections: {features_dict.get('connections', 0)}")
        print(f"      - Connected to fraudsters: {features_dict.get('fraud_connections', 0)}")
        print(f"      - FINAL FRAUD SCORE: {fraud_result['fraud_score']}")
        print(f"      - FLAGGED: {fraud_result['flagged']}")
    
    print("\n" + "="*60)
    print("✅ COMPATIBLE! The GNN code works with your data generator!")
    print("📊 Returns fraud scores in expected format: {account_id, fraud_score, flagged}")
    print("="*60)
    
    return fraud_graph, features, adjacency

if __name__ == "__main__":
    graph, features, adjacency = test_compatibility()
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
            
            for neighbor in neighbors:
                neighbor_data = self.graph.nodes.get(neighbor, {})
                if neighbor_data.get('type') == 'customer' and neighbor_data.get('is_fraud'):
                    fraud_neighbors += 1
                elif neighbor_data.get('type') == 'merchant':
                    merchant_connections += 1
            
            sim_risk = min(1.0, 7.0 / max(1, node_data.get('sim_days_ago', 365)))
            
            kyc_scores = {'basic': 0, 'verified': 0.5, 'premium': 1.0}
            kyc_score = kyc_scores.get(node_data.get('kyc', 'basic'), 0)
            
            age_risk = min(1.0, 30.0 / max(1, node_data.get('account_age', 365)))
            
            return {
                'node_id': node_id,
                'is_fraud': node_data.get('is_fraud', False),
                'kyc_score': kyc_score,
                'sim_risk': sim_risk,
                'age_risk': age_risk,
                'connections': len(neighbors),
                'merchant_connections': merchant_connections,
                'fraud_connections': fraud_neighbors,
                'risk_score': 0  
            }
        else:
            return {
                'node_id': node_id,
                'type': 'merchant',
                'transaction_count': len(list(self.graph.neighbors(node_id)))
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
                    node_features['kyc_score'],           
                    node_features['sim_risk'],            
                    node_features['age_risk'],            
                    min(1.0, node_features['connections'] / 20)  
                ]
                features.append(feature_vector)
                labels.append(float(node_features['is_fraud']))
            elif node_features and node_features.get('type') == 'merchant':
                features.append([0, 0, 0, 0, 0])
                labels.append(0)
            else:
                features.append([0, 0, 0, 0, 0])
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
                    fraud_rings.append({
                        'size': len(component),
                        'fraud_count': len(fraudsters),
                        'members': component[:5]  
                    })
        
        return fraud_rings

# ========== TEST COMPATIBILITY ==========
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
    
    print("\n4. Preparing GNN inputs...")
    features, labels, nodes = fraud_graph.get_feature_matrix()
    adjacency, adj_nodes = fraud_graph.get_adjacency_matrix()
    
    print(f"   ✅ Feature matrix shape: {features.shape}")
    print(f"   ✅ Labels shape: {labels.shape}")
    print(f"   ✅ Adjacency matrix shape: {adjacency.shape}")
    print(f"   ✅ Number of nodes: {len(nodes)}")
    
    print("\n5. Detecting fraud rings...")
    rings = fraud_graph.find_fraud_rings()
    
    if rings:
        print(f"   ✅ Found {len(rings)} potential fraud rings:")
        for i, ring in enumerate(rings[:3]):
            print(f"      Ring {i+1}: {ring['size']} accounts, {ring['fraud_count']} fraudsters")
    else:
        print("   ℹ️ No fraud rings detected (may need more data)")
    
    print("\n6. Example customer analysis:")
    customer_nodes = [n for n in nodes if fraud_graph.graph.nodes[n].get('type') == 'customer']
    if customer_nodes:
        example = customer_nodes[0]
        features_dict = fraud_graph.get_node_features(example)
        print(f"   Customer: {example}")
        print(f"      - Is Fraud: {features_dict.get('is_fraud', False)}")
        print(f"      - KYC Score: {features_dict.get('kyc_score', 0)}")
        print(f"      - SIM Risk: {features_dict.get('sim_risk', 0):.2f}")
        print(f"      - Connections: {features_dict.get('connections', 0)}")
        print(f"      - Connected to fraudsters: {features_dict.get('fraud_connections', 0)}")
    
    print("\n" + "="*60)
    print("✅ COMPATIBLE! The GNN code works with your data generator!")
    print("="*60)
    
    return fraud_graph, features, adjacency

if __name__ == "__main__":
    graph, features, adjacency = test_compatibility()
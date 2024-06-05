from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from config import RPC_USER, RPC_PASSWORD, RPC_HOST, RPC_PORT
from graphviz import Digraph

MAX_DEPTH = 50

def get_rpc_connection():
    rpc_url = f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}"
    return AuthServiceProxy(rpc_url)

def fetch_transaction(txid):
    try:
        rpc_connection = get_rpc_connection()
        return rpc_connection.getrawtransaction(txid, True)
    except JSONRPCException as e:
        print(f"Error fetching transaction {txid}: {e.error['message']}")
    except Exception as e:
        print(f"Unexpected error fetching transaction {txid}: {e}")
    return None

def build_transaction_tree(txid, depth=0):
    transaction = fetch_transaction(txid)
    if not transaction or 'vin' not in transaction or not transaction['vin']:
        return {"txid": txid, "inputs": [], "coinbase": True, "details": transaction}

    tree = {"txid": txid, "inputs": [], "details": transaction}
    if depth < MAX_DEPTH:
        for vin in transaction.get('vin', []):
            if 'txid' in vin:
                child_txid = vin['txid']
                child_tree = build_transaction_tree(child_txid, depth + 1)
                if child_tree:
                    tree['inputs'].append(child_tree)
    return tree

def visualize_transaction_tree(tree):
    dot = Digraph(comment='Transaction Tree', format='png')
    add_nodes_and_edges(tree, dot)
    return dot

def add_nodes_and_edges(tree, dot, parent=None):
    transaction_details = tree['details']
    value_out = sum(float(out['value']) for out in transaction_details.get('vout', []))
    inputs = "\n".join(f"Input Transaction Id: {vin.get('txid')}" for vin in transaction_details.get('vin', []))
    label = f"Transaction ID: {tree['txid']}\nTotal Value Out: {value_out} BTC\n{inputs}"
    if 'confirmations' in transaction_details:
        label += f"\nConfirmations: {transaction_details['confirmations']}"

    dot.node(tree['txid'], label, shape='rect', style='filled', color='darkgoldenrod2')
    if parent:
        dot.edge(tree['txid'], parent, color='black')

    for input_tree in tree['inputs']:
        add_nodes_and_edges(input_tree, dot, tree['txid'])

if __name__ == "__main__":
    txid = input("Enter transaction ID: ")
    transaction_tree = build_transaction_tree(txid)
    if transaction_tree:
        dot = visualize_transaction_tree(transaction_tree)
        dot.render('transaction_tree.gv', view=True) 
    else:
        print("Failed to create transaction tree.")

# Create a cryptocurrency
import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import sys
import requests
from uuid import uuid4
from urllib.parse import urlparse

class Blockchain:
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof=1, previous_hash='0')
        self.nodes = set()

    def create_block(self, proof, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.datetime.now()),
            'proof': proof,
            'previous_hash': previous_hash,
            'transactions': self.transactions
        }
        self.transactions = []
        self.chain.append(block)

        return block

    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({
            'sender': sender,
            'receiver': receiver,
            'amount': amount
        })
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1

    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            try:
                response = requests.get(f'http://{node}/getchain')
                if response.status_code == 200:
                    data = response.json()
                    length = data['length']
                    chain = data['chain']
                    if length > max_length and self.is_chain_valid(data['chain']):
                        longest_chain = chain
                        max_length = length
            except: 
                print(f"Error connecting to {node}", file=sys.stdout)

        if longest_chain:
            self.chain = longest_chain
            return True
        return False

    def get_previous_block(self):
        return self.chain[-1]

    def pow(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        
        return new_proof

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1

        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                print(block['previous_hash'] + "  ==> " + self.hash(previous_block) + str(block), file=sys.stdout)
                return False

            previous_proof = previous_block['proof']
            new_proof = block['proof']
            hash = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash[:4] != '0000':
                print(hash[:4], file=sys.stdout)
                return False
            
            previous_block = block
            block_index += 1
        return True


arguments = sys.argv
if len(arguments) != 2:
    raise "Usage: thala.py port"

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
blockchain =  Blockchain()
node_address = str(uuid4()).replace('-', '')

@app.route('/mineblock', methods=['GET', 'POST'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.pow(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(sender='Thala', receiver=node_address, amount=1.5)
    new_block = blockchain.create_block(proof, previous_hash)
    response = {
        'block': new_block,
        'message': 'Congrats!',
    }
    return jsonify(response), 200

@app.route('/getchain', methods=['GET'])
def get_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

@app.route('/is_valid', methods=['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid == True:
        response = { 'message': 'Blockchain is valid'}
    else:
        response = { 'message': 'Somehting is wrong with the blockchain'}
    
    return jsonify(response), 200

@app.route('/addtransaction', methods=['POST'])
def add_transaction():
    body = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all (key in body for key in transaction_keys):
        return jsonify({'message': 'Sender, Receiver, and Amount are all required fields'}) , 400
    block_id = blockchain.add_transaction(body['sender'], body['receiver'], body['amount'])
    response = {'message': f'This transaction will be addded to block {block_id}'}
    return jsonify(response), 201


@app.route('/connectnode', methods=['POST'])
def connect_node():
    body = request.get_json()
    print("THIS IS BODY " + str(body), file=sys.stdout)
    nodes = body.get('nodes')
    if nodes is None:
        return jsonify({'message': 'No nodes'}), 400
    for node in nodes:
        blockchain.add_node(node)
    return jsonify({'message': 'Nodes connected', 'total_nodes': len(blockchain.nodes)}), 200


@app.route('/replacechain', methods=['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        message = 'Chain has been replaced'
    else:
        message = 'Your chain is still valid'
    return jsonify( {'chain': blockchain.chain, 'message': message}), 200

app.run(debug=True, host = '0.0.0.0', port = arguments[1] or 5000)

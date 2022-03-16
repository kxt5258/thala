# Create a general blockchain
import datetime
import hashlib
import json
from flask import Flask, jsonify
import sys

class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_block(proof=1, previous_hash='0')

    def create_block(self, proof, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.datetime.now()),
            'proof': proof,
            'previous_hash': previous_hash
        }
        self.chain.append(block)

        return block

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

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
blockchain =  Blockchain()

@app.route('/mineblock', methods=['GET', 'POST'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.pow(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    new_block = blockchain.create_block(proof, previous_hash)
    response = {
        'block': new_block,
        'message': 'Congrats!',
    }
    return jsonify(response), 200, {'ContentType':'application/json'} 

@app.route('/getchain', methods=['GET'])
def get_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200,  {'ContentType':'application/json'} 

@app.route('/is_valid', methods=['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid == True:
        response = { 'message': 'Blockchain is valid'}
    else:
        response = { 'message': 'Somehting is wrong with the blockchain'}
    
    return jsonify(response), 200, {'ContentType':'application/json'} 


app.run(host = '0.0.0.0', port = 5000)

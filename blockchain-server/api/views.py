from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
import requests
import json
import datetime
from django.views.decorators.csrf import csrf_exempt
from .blockchain import Blockchain, Block


blockchain = Blockchain()
blockchain.create_genesis_block()

peers = set()


def consensus():
    global blockchain
    longest_chain = None
    current_len = len(blockchain.chain)

    for node in peers:
        response = requests.get('{}chain'.format(node))
        length = response.json()['length']
        chain = response.json()['chain']
        if length > current_len and blockchain.check_chain_validity(chain):
            current_len = length
            longest_chain = chain

    if longest_chain:
        blockchain = longest_chain
        return True

    return False


def announce_new_block(block):
    for peer in peers:
        url = f"{peer}add_block/"
        headers = {'Content-Type': "application/json"}
        requests.post(url, data=json.dumps(block.__dict__), headers=headers)


def create_chain_from_dump(chain_dump):
    generated_blockchain = Blockchain()
    generated_blockchain.create_genesis_block()
    for idx, block_data in enumerate(chain_dump):
        if idx == 0:
            continue
        block = Block(block_data["index"],  block_data["transactions"], block_data["timestamp"], block_data["previous_hash"], block_data["nonce"])
        proof = block_data['hash']
        added = generated_blockchain.add_block(block, proof)
        if not added:
            raise Exception("The chain dump is tampered!!")
    return generated_blockchain


@api_view(['POST'])
@csrf_exempt
def new_transactions(request):
    transaction_data = request.data
    print(transaction_data)
    required_fields = ["candidate", "voterhash"]

    for field in required_fields:
        if not transaction_data.get(field):
            return Response({'error': 'Invalid transaction data'}, status=404) 

    if (transaction_data["voterhash"] in blockchain.voted):
        return Response({'error': 'You cannot vote more than once'}, status=400)

    transaction_data["timestamp"] = str(datetime.datetime.now())
    blockchain.add_new_transaction(transaction_data)

    return Response("Success", status=201)


@api_view(['GET'])
@csrf_exempt
def get_chain(request):
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    data = {
        "length": len(chain_data),
        "chain": chain_data,
        "peers": list(peers)
    }
    return Response(data, status=200)


@api_view(['GET'])
@csrf_exempt
def mine_block(request):
    result = blockchain.mine()
    if not result:
        return Response("No transactions in queue to mine", status=404)
    else:
        chain_length = len(blockchain.chain)
        consensus()
        if chain_length == len(blockchain.chain):
            announce_new_block(blockchain.last_block)
        return Response(f"Block #{blockchain.last_block.index} is mined. Your vote is now added to the blockchain", status=201)


@api_view(['POST'])
@csrf_exempt
def register_new_peers(request):
    node_address = request.data["node_address"]
    if not node_address:
        return Response("Invalid data", status=400)
    peers.add(node_address)
    peers.add(str(request.build_absolute_uri('/')))
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    data = {
        "length": len(chain_data),
        "chain": chain_data,
        "peers": list(peers)
    }
    return Response(data, status=200)


@api_view(['POST'])
@csrf_exempt
def register_with_existing_node(request):
    node_address = request.data["node_address"]
    if not node_address:
        return Response("Invalid data", status=400)
    print("host: ", request.build_absolute_uri('/'))
    data = {"node_address": request.build_absolute_uri('/')}
    headers = {'Content-Type': "application/json"}

    response = requests.post(node_address + "/register_node/", data=json.dumps(data), headers=headers)
    if response.status_code == 200:
        global blockchain
        global peers
        chain_dump = response.json()['chain']
        blockchain = create_chain_from_dump(chain_dump)
        peers.update(response.json()['peers'])
        return Response("Registration successful", status=200)
    else:
        return Response(response.content, status= response.status_code)


@api_view(['POST'])
@csrf_exempt
def verify_and_add_block(request):
    block_data = request.data
    block = Block(block_data["index"],  block_data["transactions"], block_data["timestamp"], block_data["previous_hash"], block_data["nonce"])
    proof = block_data['hash']
    added = blockchain.add_block(block, proof)

    if not added:
        return Response("The block was discarded by the node", status=400)
    return Response("Block added to the chain", status=201)


@api_view(['GET'])
@csrf_exempt
def pending_transactions(requests):
    data = blockchain.unconfirmed_transactions
    return Response(data, status=200)


@api_view(['GET'])
@csrf_exempt
def check_if_chain_tampered(request):
    try:
        result = blockchain.check_chain_validity(blockchain.chain)
    except Exception as e:
        raise Exception(f"Problem while calling method check_chain_validity(): {e}")

    if result:
        return Response("Votes are not tampered", status=200)
    else:
        return Response("Votes are tampered", status=400)
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


def consensus():
    global blockchain
    print("block::chain ::::::::::", blockchain.chain)
    longest_chain, current_length = None, len(blockchain.chain)

    for node in blockchain.nodes:
        response = requests.get(f'{node}/chain')
        length = response.json()['length']
        print("length::", length)
        chain_json = response.json()['chain']
        print("dump::", chain_json)
        formatted_chain = Blockchain()
        formatted_chain.create_genesis_block()
        formatted_chain.chain = list(
            map(lambda block_json: Block.from_json(block_json), chain_json)
        )
        print("formatted chain::", formatted_chain.chain)
        # chain_json = json.dumps(chain_json)
        if length > current_length and blockchain.check_chain_validity(formatted_chain.chain):
        # result = blockchain.check_chain_validity(formatted_chain.chain)
        # if result:
            print("inside consensusssssssssssssssssssssssssssssssssssss")
            print("after::", formatted_chain.chain)
            current_length, longest_chain = length, formatted_chain.chain

    if longest_chain:
        print("finally::", longest_chain)
        blockchain.chain = longest_chain
        return True

    return False


def announce_new_block(block):
    for peer in blockchain.nodes:
        url = f'{peer}/add_block/'
        headers = {'Content-Type': 'application/json'}
        requests.post(url, data=json.dumps(block.__dict__), headers=headers)


def create_chain_from_dump(chain_dump):
    generated_blockchain = Blockchain()
    generated_blockchain.create_genesis_block()
    for i, block_data in enumerate(chain_dump):
        if i == 0:
            continue
        block = Block(block_data["index"],
                      block_data["transactions"],
                      block_data["timestamp"],
                      block_data["previous_hash"],
                      block_data["nonce"])
        proof = block_data['blockhash']
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

    if transaction_data["voterhash"] in blockchain.already_voted:
        return Response({'error': 'You cannot vote more than once'}, status=400)

    transaction_data["timestamp"] = str(datetime.datetime.now())
    added = blockchain.add_new_transaction(transaction_data)

    if not added:
        return Response({'error': 'Your vote is already in queue'}, status=404)

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
        "peers": blockchain.nodes
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
        backup_chain = blockchain.chain
        consensus()
        print("in mine_block: ")
        print(f"chain: {backup_chain}")
        print(f"blockchain.chain: {blockchain.chain}")
        print(f"chain length: {chain_length} and blockchain.chain: {len(blockchain.chain)}")
        if chain_length == len(blockchain.chain):
            print("inside announce")
            announce_new_block(blockchain.last_block)
        return Response(f"Block #{blockchain.last_block.index} is mined. Your vote is now added to the blockchain",
                        status=201)


@api_view(['POST'])
@csrf_exempt
def register_new_peers(request):
    node_address = request.data["node_address"]
    if not node_address:
        return Response("Invalid data", status=400)
    blockchain.add_peer(node_address[:-1])
    # print(f"Host: {str(request.build_absolute_uri('/'))} and Peer: {node_address}")
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    data = {
        "length": len(chain_data),
        "chain": chain_data,
        "peers": list(blockchain.nodes)
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

    response = requests.post(f'{node_address}/register_node/', data=json.dumps(data), headers=headers)
    if response.status_code == 200:
        global blockchain
        chain_dump = response.json()['chain']
        blockchain = create_chain_from_dump(chain_dump)
        blockchain.add_peer(node_address)
        return Response("Registration successful", status=200)
    else:
        return Response(response.content, status=response.status_code)


@api_view(['POST'])
@csrf_exempt
def verify_and_add_block(request):
    block_data = request.data
    block = Block(block_data["index"],
                  block_data["transactions"],
                  block_data["timestamp"],
                  block_data["previous_hash"],
                  block_data["nonce"])
    proof = block_data['blockhash']
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


@api_view(['GET'])
@csrf_exempt
def reset_blockchain(request):
    try:
        blockchain.chain = []
        blockchain.create_genesis_block()
        return Response("Reset successful", status=200)
    except Exception as e:
        raise Exception(f"An error occurred while replacing chain: {e}")


@api_view(['GET'])
def tamper_block(request):
    global blockchain
    for i, block in enumerate(blockchain.chain):
        if i == 1:
            block.transactions[0]['candidate'] = 'Hacker'
    return Response('Blockchain hacked successfully')


@api_view(['GET'])
def sync_with_honest_nodes(request):
    global blockchain
    if not len(blockchain.nodes):
        return Response('Current node is not connected with any other nodes', status=404)
    print("block::chain inside sync::::::::::", blockchain.chain)
    longest_chain, current_length = None, len(blockchain.chain)

    for node in blockchain.nodes:
        response = requests.get(f'{node}/chain')
        length = response.json()['length']
        print("length::", length)
        chain_json = response.json()['chain']
        print("dump::", chain_json)
        formatted_chain = Blockchain()
        formatted_chain.create_genesis_block()
        formatted_chain.chain = list(
            map(lambda block_json: Block.from_json(block_json), chain_json)
        )
        print("formatted chain::", formatted_chain.chain)
        if length >= current_length and blockchain.check_chain_validity(formatted_chain.chain):
            print("inside consensusssssssssssssssssssssssssssssssssssss")
            print("after::", formatted_chain.chain)
            current_length, longest_chain = length, formatted_chain.chain

    if longest_chain:
        print("finally::", longest_chain)
        blockchain.chain = longest_chain
        return Response('Synchronized with honest nodes', status=200)

    return Response('All nodes are corrupt', status=404)

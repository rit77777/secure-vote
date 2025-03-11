from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

import datetime

from .serializers import (TransactionSerializer, BlockSerializer, ChainSerializer,
                         NodeRegistrationSerializer, MessageResponseSerializer,
                         ErrorResponseSerializer)

from .blockchain import Blockchain, Block
from .helpers import consensus, announce_new_block, create_chain_from_dump, sync_with_nodes

# Initialize blockchain
blockchain = Blockchain()
blockchain.create_genesis_block()


class TransactionView(APIView):
    """
    API view for handling new transaction requests
    """
    def post(self, request):
        serializer = TransactionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                ErrorResponseSerializer({'error': serializer.errors}).data,
                status=status.HTTP_400_BAD_REQUEST
            )

        # Early return for duplicate votes
        if serializer.validated_data["voterhash"] in blockchain.already_voted:
            return Response(
                ErrorResponseSerializer({'error': 'You cannot vote more than once'}).data,
                status=status.HTTP_400_BAD_REQUEST
            )

        transaction_data = serializer.validated_data
        transaction_data["timestamp"] = str(datetime.datetime.now())
        added = blockchain.add_new_transaction(transaction_data)

        # Early return for transaction already in queue
        if not added:
            return Response(
                ErrorResponseSerializer({'error': 'Your vote is already in queue'}).data,
                status=status.HTTP_409_CONFLICT
            )

        return Response(
            MessageResponseSerializer({'message': 'Vote successfully added'}).data,
            status=status.HTTP_201_CREATED
        )


class ChainView(APIView):
    """
    API view for retrieving the blockchain
    """
    def get(self, request):
        chain_data = [block.__dict__ for block in blockchain.chain]
        serializer = ChainSerializer({
            "length": len(chain_data),
            "chain": chain_data,
            "peers": list(blockchain.nodes)
        })
        return Response(serializer.data, status=status.HTTP_200_OK)


class MineBlockView(APIView):
    """
    API view for mining a new block
    """
    def get(self, request):
        # Early return if mining is already in progress
        if blockchain.is_mining:
            return Response(
                {"message": "Your block is being mined"}, 
                status=status.HTTP_200_OK
            )
        
        result = blockchain.mine()
        
        # Early return if no transactions to mine
        if not result:
            return Response(
                {"message": "No transactions in queue to mine"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        prev_length = len(blockchain.chain)
        chain_length = len(blockchain.chain)
        
        consensus(blockchain)
        
        if chain_length == len(blockchain.chain):
            for i, block in enumerate(blockchain.chain):
                if i >= prev_length:
                    announce_new_block(blockchain, block)
        
        return Response(
            {"message": f"Block #{blockchain.last_block.index} is mined. Your vote is now added to the blockchain"},
            status=status.HTTP_201_CREATED
        )


class RegisterNodeView(APIView):
    """
    API view for registering new peer nodes
    """
    def post(self, request):
        serializer = NodeRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                ErrorResponseSerializer({'error': serializer.errors}).data,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        node_address = serializer.validated_data["node_address"]
        
        blockchain.add_peer(node_address[:-1])
        chain_data = [block.__dict__ for block in blockchain.chain]
        
        data = {
            "length": len(chain_data),
            "chain": chain_data,
            "peers": list(blockchain.nodes)
        }
        return Response(data, status=status.HTTP_200_OK)


class RegisterWithNodeView(APIView):
    """
    API view for registering with an existing node
    """
    def post(self, request):
        serializer = NodeRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                ErrorResponseSerializer({'error': serializer.errors}).data,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        node_address = serializer.validated_data["node_address"]
        
        import json
        import requests
        
        data = {"node_address": request.build_absolute_uri('/')}
        headers = {'Content-Type': "application/json"}
        
        try:
            response = requests.post(
                f'{node_address}/register_node/', 
                data=json.dumps(data), 
                headers=headers
            )
            
            if response.status_code == 200:
                global blockchain
                chain_dump = response.json()['chain']
                blockchain = create_chain_from_dump(chain_dump)
                blockchain.add_peer(node_address)
                return Response(
                    {"message": "Registration successful"}, 
                    status=status.HTTP_200_OK
                )
            
            return Response(
                response.json(), 
                status=response.status_code
            )
            
        except requests.RequestException as e:
            return Response(
                {"error": f"Connection error: {str(e)}"}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class AddBlockView(APIView):
    """
    API view for verifying and adding a block
    """
    def post(self, request):
        serializer = BlockSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                ErrorResponseSerializer({'error': serializer.errors}).data,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        block_data = serializer.validated_data
        
        block = Block(
            block_data["index"], 
            block_data["transactions"], 
            block_data["timestamp"],
            block_data["previous_hash"], 
            block_data["nonce"]
        )
        proof = block_data['blockhash']
        
        added = blockchain.add_block(block, proof)
        
        if not added:
            return Response(
                {"error": "The block was discarded by the node"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(
            {"message": "Block added to the chain"}, 
            status=status.HTTP_201_CREATED
        )


class PendingTransactionsView(APIView):
    """
    API view for retrieving pending transactions
    """
    def get(self, request):
        return Response(
            blockchain.unconfirmed_transactions, 
            status=status.HTTP_200_OK
        )


class ChainValidityView(APIView):
    """
    API view for checking if the chain has been tampered with
    """
    def get(self, request):
        try:
            result = blockchain.check_chain_validity(blockchain.chain)
            
            if result:
                return Response(
                    {"message": "Votes are not tampered"}, 
                    status=status.HTTP_200_OK
                )
            
            return Response(
                {"error": "Votes are tampered"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            return Response(
                {"error": f"Error checking chain validity: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ResetBlockchainView(APIView):
    """
    API view for resetting the blockchain
    """
    def get(self, request):
        try:
            blockchain.chain = []
            blockchain.create_genesis_block()
            return Response(
                {"message": "Reset successful"}, 
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Error resetting blockchain: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TamperBlockView(APIView):
    """
    API view for tampering with a block (for testing purposes)
    """
    def get(self, request):
        if len(blockchain.chain) <= 1:
            return Response(
                {"error": "No blocks in blockchain to tamper with"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        block = blockchain.chain[1]
        block.transactions[0]['candidate'] = 'Hacker'
        
        return Response(
            {"message": "Blockchain hacked successfully"}, 
            status=status.HTTP_200_OK
        )


class SyncWithNodesView(APIView):
    """
    API view for synchronizing with honest nodes
    """
    def get(self, request):
        if not blockchain.nodes:
            return Response(
                {"error": "Current node is not connected with any other nodes"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        success, message = sync_with_nodes(blockchain)
        
        if success:
            return Response(
                {"message": message}, 
                status=status.HTTP_200_OK
            )
        
        return Response(
            {"error": message}, 
            status=status.HTTP_404_NOT_FOUND
        )

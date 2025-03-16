import datetime
import json
import logging
from hashlib import sha256
from typing import List, Set, Dict, Any, Optional
from django.db import transaction
from .models import IBlockchain, Block as BlockModel

logger = logging.getLogger(__name__)

class BlockchainPersistent(IBlockchain):
    def __init__(self):
        self.unconfirmed_transactions: List[Dict] = []
        self.already_voted: Set[str] = set()
        self.nodes: Set[str] = set()
        self.is_mining: bool = False

    def create_genesis_block(self) -> None:
        """Create the first block in the chain"""
        if BlockModel.objects.exists():
            return

        genesis_block = BlockModel(
            index=0,
            transactions=[],
            timestamp='0',
            previous_hash='0',
            nonce=0
        )
        genesis_block.blockhash = self._compute_hash(genesis_block)
        genesis_block.save()

    @property
    def last_block(self) -> BlockModel:
        """Get the most recent block in the chain"""
        try:
            return BlockModel.objects.latest('index')
        except BlockModel.DoesNotExist:
            raise ValueError("Chain is empty")

    def add_peer(self, peer: str) -> None:
        """Add a new peer node to the network"""
        if not peer:
            logger.warning("Attempted to add empty peer")
            return
        self.nodes.add(peer)
        logger.info(f"Added peer: {peer}")

    def add_block(self, block: BlockModel, proof: str) -> bool:
        """Add a block to the chain if it's valid"""
        try:
            previous_block = self.last_block
        except ValueError:
            logger.error("Cannot add block to empty chain")
            return False

        if previous_block.blockhash != block.previous_hash:
            logger.warning("Block rejected: previous hash mismatch")
            return False

        if not self._is_valid_proof(block, proof):
            logger.warning("Block rejected: invalid proof")
            return False

        block.blockhash = proof
        block.save()

        if block.transactions and 'voterhash' in block.transactions[0]:
            self.already_voted.add(block.transactions[0]['voterhash'])

        logger.info(f"Added block #{block.index} to the chain")
        return True

    def proof_of_work(self, block: BlockModel) -> str:
        """Find a proof that satisfies our proof of work algorithm"""
        block.nonce = 0
        computed_hash = self._compute_hash(block)

        while not computed_hash.startswith('0' * self.DIFFICULTY):
            block.nonce += 1
            computed_hash = self._compute_hash(block)

        logger.debug(f"Found proof of work: {computed_hash} with nonce: {block.nonce}")
        return computed_hash

    def add_new_transaction(self, transaction: Dict) -> bool:
        """Add a new transaction to the list of unconfirmed transactions"""
        voter_hash = transaction.get('voterhash')
        if not voter_hash:
            logger.warning("Transaction rejected: missing voterhash")
            return False

        for unconfirmed_transaction in self.unconfirmed_transactions:
            if unconfirmed_transaction.get('voterhash') == voter_hash:
                logger.warning(f"Transaction rejected: voter {voter_hash} already has pending transaction")
                return False

        self.unconfirmed_transactions.append(transaction)
        logger.info(f"Added new transaction for voter: {voter_hash}")
        return True

    def check_chain_validity(self, chain: List[BlockModel]) -> bool:
        """Check if the entire blockchain is valid"""
        if not chain:
            logger.warning("Cannot validate empty chain")
            return False

        previous_hash = '0'

        for block in chain:
            block_hash = block.blockhash
            delattr(block, 'blockhash')

            if not self._is_valid_proof(block, block_hash) or previous_hash != block.previous_hash:
                block.blockhash = block_hash
                return False

            block.blockhash = block_hash
            previous_hash = block_hash

        return True

    def mine(self) -> bool:
        """Mine pending transactions and add them to the blockchain"""
        if not self.unconfirmed_transactions:
            return False

        if self.is_mining:
            return False

        try:
            self.is_mining = True
            last_block = self.last_block

            new_block = BlockModel(
                index=last_block.index + 1,
                transactions=self.unconfirmed_transactions,
                timestamp=str(datetime.datetime.now()),
                previous_hash=last_block.blockhash
            )

            proof = self.proof_of_work(new_block)
            self.add_block(new_block, proof)
            self.unconfirmed_transactions = []
            return True

        finally:
            self.is_mining = False

    def _compute_hash(self, block: BlockModel) -> str:
        """Compute SHA-256 hash of the block"""
        block_dict = {
            'index': block.index,
            'transactions': block.transactions,
            'timestamp': block.timestamp,
            'previous_hash': block.previous_hash,
            'nonce': block.nonce
        }
        block_string = json.dumps(block_dict, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()

    def _is_valid_proof(self, block: BlockModel, block_hash: str) -> bool:
        """Check if block_hash is valid hash of block and satisfies difficulty criteria"""
        if not block_hash.startswith('0' * self.DIFFICULTY):
            return False

        return block_hash == self._compute_hash(block)
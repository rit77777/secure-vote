import datetime
import json
import logging
from hashlib import sha256
from typing import List, Set, Dict, Any, Optional
from .models import IBlockchain, Block as BlockModel

logger = logging.getLogger(__name__)

class Block:
    def __init__(self, index: int, transactions: List[Dict], timestamp: Any, 
                 previous_hash: str, nonce: int = 0, blockhash: str = '0'):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.blockhash = blockhash

    def compute_hash(self) -> str:
        """Compute SHA-256 hash of the block"""
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()

    @staticmethod
    def from_json(block_json: Dict) -> 'Block':
        """Create a Block instance from JSON data"""
        return Block(**block_json)


class BlockchainInMemory(IBlockchain):
    # Class constants
    DIFFICULTY = 4
    
    def __init__(self):
        self.unconfirmed_transactions: List[Dict] = []
        self.chain: List[Block] = []
        self.already_voted: Set[str] = set()
        self.nodes: Set[str] = set()
        self.is_mining: bool = False

    def create_genesis_block(self) -> None:
        """Create the first block in the chain"""
        genesis_block = Block(0, [], 0, "0")
        genesis_block.blockhash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self) -> Block:
        """Get the most recent block in the chain"""
        if not self.chain:
            raise ValueError("Chain is empty")
        return self.chain[-1]

    def add_peer(self, peer: str) -> None:
        """Add a new peer node to the network"""
        if not peer:
            logger.warning("Attempted to add empty peer")
            return
        self.nodes.add(peer)
        logger.info(f"Added peer: {peer}")

    def add_block(self, block: Block, proof: str) -> bool:
        """
        Add a block to the chain if it's valid
        
        Args:
            block: The block to add
            proof: The proof of work for the block
            
        Returns:
            bool: True if block was added, False otherwise
        """
        # Early return if chain is empty
        if not self.chain:
            logger.error("Cannot add block to empty chain")
            return False
            
        previous_hash = self.last_block.blockhash
        logger.debug(f"Previous hash: {previous_hash}, Block previous hash: {block.previous_hash}")
        
        # Early return if previous hash doesn't match
        if previous_hash != block.previous_hash:
            logger.warning("Block rejected: previous hash mismatch")
            return False

        # Early return if proof is invalid
        if not self._is_valid_proof(block, proof):
            logger.warning("Block rejected: invalid proof")
            return False

        # If we get here, the block is valid
        block.blockhash = proof
        self.chain.append(block)
        
        # Add voter to already voted set if transactions exist
        if block.transactions and 'voterhash' in block.transactions[0]:
            self.already_voted.add(block.transactions[0]['voterhash'])
            
        logger.info(f"Added block #{block.index} to the chain")
        return True

    def proof_of_work(self, block: Block) -> str:
        """
        Find a proof that satisfies our proof of work algorithm
        
        Args:
            block: The block to find proof for
            
        Returns:
            str: The proof (hash) that satisfies our difficulty requirement
        """
        block.nonce = 0
        computed_hash = block.compute_hash()
        
        while not computed_hash.startswith('0' * self.DIFFICULTY):
            block.nonce += 1
            computed_hash = block.compute_hash()
            
        logger.debug(f"Found proof of work: {computed_hash} with nonce: {block.nonce}")
        return computed_hash

    def add_new_transaction(self, transaction: Dict) -> bool:
        """
        Add a new transaction to the list of unconfirmed transactions
        
        Args:
            transaction: The transaction to add
            
        Returns:
            bool: True if transaction was added, False otherwise
        """
        # Early return if transaction already exists
        voter_hash = transaction.get('voterhash')
        if not voter_hash:
            logger.warning("Transaction rejected: missing voterhash")
            return False
            
        # Check if voter has already voted in unconfirmed transactions
        for unconfirmed_transaction in self.unconfirmed_transactions:
            if unconfirmed_transaction.get('voterhash') == voter_hash:
                logger.warning(f"Transaction rejected: voter {voter_hash} already has pending transaction")
                return False
                
        self.unconfirmed_transactions.append(transaction)
        logger.info(f"Added new transaction for voter: {voter_hash}")
        return True

    def _is_valid_proof(self, block: Block, block_hash: str) -> bool:
        """
        Check if block_hash is valid hash of block and satisfies difficulty criteria
        
        Args:
            block: The block to validate
            block_hash: The hash to check
            
        Returns:
            bool: True if the proof is valid, False otherwise
        """
        # Check if hash meets difficulty requirement
        if not block_hash.startswith('0' * self.DIFFICULTY):
            return False
            
        # Check if hash matches block's computed hash
        return block_hash == block.compute_hash()

    def check_chain_validity(self, chain: List[Block]) -> bool:
        """
        Check if the entire blockchain is valid
        
        Args:
            chain: The blockchain to check
            
        Returns:
            bool: True if chain is valid, False otherwise
        """
        if not chain:
            logger.warning("Cannot validate empty chain")
            return False
            
        previous_hash = '0'
        
        for i, block in enumerate(chain):
            block_hash = block.blockhash
            
            # Handle genesis block separately
            if i == 0:
                previous_hash = block_hash
                continue
                
            # Save original hash
            original_hash = block.blockhash
            
            # Temporarily set hash to zero for validation
            block.blockhash = '0'
            
            # Check if block is valid
            if not self._is_valid_proof(block, original_hash) or previous_hash != block.previous_hash:
                # Restore original hash before returning
                block.blockhash = original_hash
                logger.warning(f"Chain validation failed at block {i}")
                return False
                
            # Restore hash and update previous_hash for next iteration
            block.blockhash = original_hash
            previous_hash = original_hash
            
        return True

    def mine(self) -> bool:
        """
        Mine pending transactions and add them to the blockchain
        
        Returns:
            bool: True if mining was successful, False otherwise
        """
        # Early return if no transactions to mine
        if not self.unconfirmed_transactions:
            logger.info("No transactions to mine")
            return False

        self.is_mining = True
        
        try:
            # Process each transaction one by one
            transactions_to_process = self.unconfirmed_transactions.copy()
            
            for transaction in transactions_to_process:
                # Create a new block with just this transaction
                prev_block = self.last_block
                new_block = Block(
                    index=prev_block.index + 1,
                    transactions=[transaction],
                    timestamp=str(datetime.datetime.now()),
                    previous_hash=prev_block.blockhash
                )
                
                # Find proof of work for this block
                proof = self.proof_of_work(new_block)
                
                # Add the block to the chain
                if self.add_block(new_block, proof):
                    # Remove the transaction from unconfirmed list
                    self.unconfirmed_transactions.remove(transaction)
                    logger.info(f"Mined transaction for voter: {transaction.get('voterhash')}")
                else:
                    logger.warning(f"Failed to add block for transaction: {transaction}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error during mining: {str(e)}")
            return False
            
        finally:
            self.is_mining = False

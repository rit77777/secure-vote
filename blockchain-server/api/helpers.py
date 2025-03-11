import json
import logging
from typing import Tuple, Optional, List
import requests
from requests.exceptions import RequestException
from .blockchain import Blockchain, Block

logger = logging.getLogger(__name__)

def fetch_chain_from_node(node: str) -> Tuple[Optional[dict], Optional[str]]:
    """
    Fetches blockchain data from a node
    Returns: Tuple of (response_data, error_message)
    """
    try:
        response = requests.get(f'{node}/chain')
        response.raise_for_status()
        return response.json(), None
    except RequestException as e:
        logger.error(f"Error fetching chain from node {node}: {str(e)}")
        return None, f"Failed to fetch chain from node: {str(e)}"

def format_chain_from_json(chain_json: List[dict]) -> Blockchain:
    """
    Creates a formatted blockchain from JSON data
    """
    formatted_chain = Blockchain()
    formatted_chain.create_genesis_block()
    formatted_chain.chain = [Block.from_json(block) for block in chain_json]
    return formatted_chain

def consensus(blockchain: Blockchain) -> bool:
    """
    Implements the consensus algorithm to ensure all nodes have the same chain
    """
    if not blockchain.nodes:
        logger.info("No nodes available for consensus")
        return False

    current_length = len(blockchain.chain)
    longest_chain = None

    for node in blockchain.nodes:
        chain_data, error = fetch_chain_from_node(node)
        if error:
            logger.warning(f"Skipping node {node}: {error}")
            continue

        try:
            formatted_chain = format_chain_from_json(chain_data['chain'])
            chain_length = chain_data['length']

            if chain_length > current_length and blockchain.check_chain_validity(formatted_chain.chain):
                current_length = chain_length
                longest_chain = formatted_chain.chain
                logger.info(f"Found longer valid chain from node {node}")
        except Exception as e:
            logger.error(f"Error processing chain from node {node}: {str(e)}")
            continue

    if longest_chain:
        blockchain.chain = longest_chain
        logger.info("Consensus achieved, chain updated")
        return True

    logger.info("No longer valid chain found")
    return False

def announce_new_block(blockchain: Blockchain, block: Block) -> None:
    """
    Announces a newly mined block to all nodes in the network
    """
    headers = {'Content-Type': 'application/json'}
    block_data = json.dumps(block.__dict__)

    for peer in blockchain.nodes:
        try:
            response = requests.post(
                f'{peer}/add_block/',
                data=block_data,
                headers=headers
            )
            response.raise_for_status()
            logger.info(f"Successfully announced block to {peer}")
        except RequestException as e:
            logger.error(f"Failed to announce block to {peer}: {str(e)}")

def create_chain_from_dump(chain_dump: List[dict]) -> Blockchain:
    """
    Creates a blockchain from a chain dump
    """
    if not chain_dump:
        raise ValueError("Empty chain dump provided")

    generated_blockchain = Blockchain()
    generated_blockchain.create_genesis_block()

    # Skip genesis block (index 0)
    for block_data in chain_dump[1:]:
        try:
            block = Block(
                block_data["index"],
                block_data["transactions"],
                block_data["timestamp"],
                block_data["previous_hash"],
                block_data["nonce"]
            )
            proof = block_data['blockhash']
            
            if not generated_blockchain.add_block(block, proof):
                raise ValueError("Invalid block detected")
                
        except KeyError as e:
            raise ValueError(f"Missing required field in block data: {str(e)}")

    return generated_blockchain

def sync_with_nodes(blockchain: Blockchain) -> Tuple[bool, str]:
    """
    Synchronizes the blockchain with honest nodes in the network
    """
    if not blockchain.nodes:
        return False, 'Current node is not connected with any other nodes'

    current_length = len(blockchain.chain)
    longest_chain = None

    for node in blockchain.nodes:
        chain_data, error = fetch_chain_from_node(node)
        if error:
            logger.warning(f"Skipping node {node} during sync: {error}")
            continue

        try:
            formatted_chain = format_chain_from_json(chain_data['chain'])
            chain_length = chain_data['length']

            if chain_length >= current_length and blockchain.check_chain_validity(formatted_chain.chain):
                current_length = chain_length
                longest_chain = formatted_chain.chain
                logger.info(f"Found valid chain from node {node}")
        except Exception as e:
            logger.error(f"Error processing chain during sync from node {node}: {str(e)}")
            continue

    if longest_chain:
        blockchain.chain = longest_chain
        return True, 'Synchronized with honest nodes'

    return False, 'No valid chains found from connected nodes'
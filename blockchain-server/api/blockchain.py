import datetime
import json
from hashlib import sha256


class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0, blockhash='0'):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.blockhash = blockhash

    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()

    @staticmethod
    def from_json(block_json):
        return Block(**block_json)


class Blockchain:
    difficulty = 4

    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []
        self.already_voted = set()
        self.nodes = set()
        self.is_mining = False

    def create_genesis_block(self):
        genesis_block = Block(0, [], 0, "0")
        genesis_block.blockhash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]

    def add_peer(self, peer):
        self.nodes.add(peer)

    def add_block(self, block, proof):
        print("inside add_block")
        previous_hash = self.last_block.blockhash
        print("add_block::previous_hash", previous_hash)
        print("add_block::block.previous_hash", block.previous_hash)

        if previous_hash != block.previous_hash:
            print("1111111111111111")
            return False

        if not Blockchain.is_valid_proof(block, proof):
            print("2222222222222222")
            return False

        block.blockhash = proof
        self.chain.append(block)
        self.already_voted.add(block.transactions[0]['voterhash'])
        return True

    @staticmethod
    def proof_of_work(block):
        block.nonce = 0
        computed_hash = block.compute_hash()

        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash

    def add_new_transaction(self, transaction):
        for unconfirmed_transaction in self.unconfirmed_transactions:
            if unconfirmed_transaction['voterhash'] == transaction['voterhash']:
                return False
        self.unconfirmed_transactions.append(transaction)
        return True

    @classmethod
    def is_valid_proof(cls, block, block_hash):
        print(f"is_valid_proof::block={block} hash={block_hash}")
        return block_hash.startswith('0' * Blockchain.difficulty) and block_hash == block.compute_hash()

    @classmethod
    def check_chain_validity(cls, chain):
        print("inside chain validity", chain)
        result, previous_hash = True, '0'
        for i, block in enumerate(chain):
            block_hash = block.blockhash
            if i == 0:
                previous_hash = block_hash
                continue
            else:
                block.blockhash = '0'
                if not cls.is_valid_proof(block, block_hash) or previous_hash != block.previous_hash:
                    result, block.blockhash = False, block_hash
                    break
                block.blockhash, previous_hash = block_hash, block_hash
        return result

    def mine(self):
        mining_queue = self.unconfirmed_transactions
        if not mining_queue:
            return False

        self.is_mining = True
        length_pending = len(mining_queue)
        for _ in range(length_pending):
            prev_block = self.last_block
            first_mining_queue_list = [mining_queue[0]]
            new_block = Block(prev_block.index + 1,
                              first_mining_queue_list,
                              str(datetime.datetime.now()),
                              prev_block.blockhash)
            proof = self.proof_of_work(new_block)
            self.add_block(new_block, proof)
            mining_queue.pop(0)
        self.is_mining = False
        return True

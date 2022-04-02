from hashlib import sha256
import datetime
import json


class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce


    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()


class Blockchain:
    difficulty = 4

    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []
        self.voted = []


    def create_genesis_block(self):
        genesis_block = Block(0, [], 0, "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)


    @property
    def last_block(self):
        return self.chain[-1]


    def add_block(self, block, proof):
        previous_hash = self.last_block.hash

        if previous_hash != block.previous_hash:
            return False

        if not Blockchain.is_valid_proof(block, proof):
            return False

        block.hash = proof
        self.chain.append(block)
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
        self.voted.append(transaction['voterhash'])
        self.unconfirmed_transactions.append(transaction)


    @classmethod
    def is_valid_proof(cls, block, block_hash):
        return (block_hash.startswith('0' * Blockchain.difficulty) and block_hash == block.compute_hash())


    @classmethod
    def check_chain_validity(cls, chain):
        result = True
        previous_hash = "0"
        i = 0
        for block in chain:
            block_hash = block.hash
            if i == 0:
                # print(f"{i} {block.__dict__}")
                previous_hash = block_hash
                i += 1
                continue
            else:
                # print(f"{i} {block.__dict__}")
                print("hash:: ", block_hash)
                delattr(block, "hash")

                if not cls.is_valid_proof(block, block_hash) or previous_hash != block.previous_hash:
                    print("Oh noooooooo block tampered (should be True)::: ", Blockchain.is_valid_proof(block, block_hash))
                    # print("previous_hash ::: ", previous_hash)
                    # print("block.previous_hash ::: ", block.previous_hash)
                    print("Oh again block tampered (should be False)::: ", previous_hash != block.previous_hash)
                    result = False
                    break

                block.hash = block_hash
                previous_hash = block_hash
                i += 1
        print("validity result:  ", result)
        return result


    def mine(self):
        if not self.unconfirmed_transactions:
            return False
        length_pending = len(self.unconfirmed_transactions)
        for _ in range(length_pending):
            prev_block = self.last_block
            first_unconfirmed_transactions_list = []
            first_unconfirmed_transactions_list.append(self.unconfirmed_transactions[0])
            new_block = Block(prev_block.index + 1, first_unconfirmed_transactions_list, str(datetime.datetime.now()), prev_block.hash)
            proof = self.proof_of_work(new_block)
            self.add_block(new_block, proof)
            self.unconfirmed_transactions.pop(0)
        return True
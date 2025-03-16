from django.db import models
from typing import List, Dict, Any, Set
from abc import ABC, abstractmethod
import json


class Block(models.Model):
    index = models.IntegerField(db_index=True)  # Added db_index for faster querying
    transactions = models.JSONField()
    timestamp = models.CharField(max_length=50)  # Store as string for compatibility
    previous_hash = models.CharField(max_length=64)
    nonce = models.IntegerField(default=0)
    blockhash = models.CharField(max_length=64, default='0')

    class Meta:
        ordering = ['index']
        indexes = [
            models.Index(fields=['index']),
        ]

    def __str__(self):
        return f'Block {self.index}'


class IBlockchain(ABC):
    DIFFICULTY = 4

    @abstractmethod
    def create_genesis_block(self) -> None:
        """Create the first block in the chain"""
        pass

    @abstractmethod
    def last_block(self) -> Any:
        """Get the most recent block in the chain"""
        pass

    @abstractmethod
    def add_peer(self, peer: str) -> None:
        """Add a new peer node to the network"""
        pass

    @abstractmethod
    def add_block(self, block: Any, proof: str) -> bool:
        """Add a block to the chain if it's valid"""
        pass

    @abstractmethod
    def proof_of_work(self, block: Any) -> str:
        """Find a proof that satisfies our proof of work algorithm"""
        pass

    @abstractmethod
    def add_new_transaction(self, transaction: Dict) -> bool:
        """Add a new transaction to the list of unconfirmed transactions"""
        pass

    @abstractmethod
    def check_chain_validity(self, chain: List[Any]) -> bool:
        """Check if the entire blockchain is valid"""
        pass

    @abstractmethod
    def mine(self) -> bool:
        """Mine pending transactions and add them to the blockchain"""
        pass

# Create your models here.


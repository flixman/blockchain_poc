"""Module for blockchain block definition and operations."""

import hashlib
from dataclasses import dataclass, field
from functools import cached_property
from time import time
from typing import Any, Self

from blockchain.transaction import Transaction


@dataclass
class Block:
    """Model a single block in a blockchain."""

    index: int
    transactions: list[Transaction]
    nonce: int
    previous_block_hash: bytes
    difficulty: int
    timestamp: int = field(default_factory=lambda: int(time()))

    @cached_property
    def transactions_merkle_root(self) -> bytes:
        """Calculate the merkle root for the transactions list."""
        hashes = [tx.hash for tx in self.transactions]

        if not hashes:
            return b"\x00" * 32

        while len(hashes) > 1:
            if len(hashes) % 2:
                hashes.append(hashes[-1])

            hashes = [hashlib.sha256(hashes[i] + hashes[i + 1]).digest() for i in range(0, len(hashes), 2)]

        return hashes[0]

    @property
    def hash(self) -> bytes:
        """Calculate the hash of the block."""
        t: bytes = (
            self.index.to_bytes(8, "big")
            + self.timestamp.to_bytes(8, "big")
            + self.transactions_merkle_root
            + self.nonce.to_bytes(8, "big")
            + self.previous_block_hash
        )
        return hashlib.sha256(t).digest()

    def __repr__(self) -> str:
        """Provide a user-friendly string for representation."""
        txs_repr = "[" + ", ".join(repr(tx) for tx in self.transactions) + "]"
        return f"Block(index={self.index}, timestamp={self.timestamp}, transactions={txs_repr}, nonce={self.nonce})"

    def to_dict(self) -> dict[str, Any]:
        """Return a view of the class as a dictionary."""
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "nonce": self.nonce,
            "previous_block_hash": self.previous_block_hash.hex(),
            "difficulty": self.difficulty,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Self:
        """Convert a given dictionary into an instance of the class."""
        txs = [Transaction.from_dict(tx) for tx in d["transactions"]]
        return cls(
            index=d["index"],
            timestamp=d["timestamp"],
            transactions=txs,
            nonce=d["nonce"],
            previous_block_hash=bytes.fromhex(d["previous_block_hash"]),
            difficulty=d["difficulty"],
        )

    def validate(self) -> bool:
        """Validat a nonce for Proof-of-Work."""
        return int.from_bytes(self.hash, "big") < 2 ** (256 - 4 * self.difficulty)

    @classmethod
    def proof_of_work(
        cls,
        last_block: Self,
        transactions: list[Transaction],
        difficulty: int = 4,
    ) -> Self:
        """Find a nonce such that the SHA-256 hash of the block header successfully validates."""
        index = last_block.index + 1

        # compute merkle root of candidate transactions
        temp_block = cls(
            index=index,
            transactions=transactions,
            nonce=0,
            previous_block_hash=last_block.hash,
            difficulty=difficulty,
        )

        while not temp_block.validate():
            temp_block.nonce += 1

        # return the fully mined block
        return temp_block

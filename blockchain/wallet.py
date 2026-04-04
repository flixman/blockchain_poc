"""Module for a wallet definition and operations."""

import hashlib

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

from blockchain.transaction import Transaction


class Wallet:
    """Model a wallet, that can sign transactions."""

    def __init__(self) -> None:
        """Initialize the private and public members"""

        self._private_key = ec.generate_private_key(ec.SECP256K1(), default_backend())
        self.public_key_bytes = self._private_key.public_key().public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint,
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, type(self)) and self._private_key == other._private_key

    @property
    def address(self) -> bytes:
        """Get the address (pubkey digest)"""
        return hashlib.sha256(self.public_key_bytes).digest()

    def new_transaction(self, recipient: bytes, amount: int, fee: int) -> Transaction:
        """Create a new signed transaction from this wallet.

        Args:
            recipient: Recipient's address (bytes).
            amount: Amount to transfer.
            fee: Transaction fee.

        Returns:
            Transaction: A new signed transaction ready for submission.
        """
        return Transaction(
            sender_pubkey=self.public_key_bytes,
            recipient=recipient,
            amount=amount,
            fee=fee,
            sender_privkey=self._private_key,
        )

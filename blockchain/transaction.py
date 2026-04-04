"""Module for a transaction definition and operations."""

import hashlib
from dataclasses import InitVar, dataclass, field, fields
from typing import Any, Optional, Self
import logging

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes


logger = logging.getLogger("Transaction")


def bytes_to_hex(b: bytes) -> str:
    """Convert a bytes object to a hexadecimal string."""
    return b.hex()


def hex_to_bytes(s: str) -> bytes:
    """Convert a hexadecimal string into a bytes object."""
    return bytes.fromhex(s)


class InvalidTransactionSignature(Exception):
    """Models an exception due to an invalid signature"""


@dataclass
class Transaction:
    """Model a transaction that can be added to a block."""

    sender_pubkey: bytes = field(metadata={"serialize": bytes_to_hex, "deserialize": hex_to_bytes})
    recipient: bytes = field(metadata={"serialize": bytes_to_hex, "deserialize": hex_to_bytes})
    amount: int
    fee: int = 0
    signature: bytes = field(default=b"", metadata={"serialize": bytes_to_hex, "deserialize": hex_to_bytes})
    sender_privkey: InitVar[Optional[ec.EllipticCurvePrivateKey]] = None

    @property
    def payload(self) -> bytes:
        """Generate the payload for transaction signing.

        The payload consists of concatenated fields: sender pubkey, recipient,
        amount (8 bytes), and fee (8 bytes). This creates the data that is
        cryptographically signed to verify transaction authenticity.

        Returns:
            bytes: Serialized transaction payload for signing.
        """
        return self.sender_pubkey + self.recipient + self.amount.to_bytes(8, "big") + self.fee.to_bytes(8, "big")

    def _validate(self):
        """Validate the transaction signature.

        Verifies that the signature was created by the sender's private key
        corresponding to sender_pubkey. Returns False if validation fails.

        Returns:
            bool: True if signature is valid, False otherwise.
        """
        pub = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), self.sender_pubkey)
        try:
            pub.verify(self.signature, self.payload, ec.ECDSA(hashes.SHA256()))
            return True
        except Exception:
            return False

    def __post_init__(self, sender_privkey: Optional[ec.EllipticCurvePrivateKey] = None):
        """If the signature is not valid, raise."""

        # if there is no private key, validate signature. Otherwise, sign
        if sender_privkey is None:
            # if both sender and signature are empty, this is a reward for a block mined
            if self.sender_pubkey == b"" and self.signature == b"":
                return

            # CHALLENGE: prevent wallet impersonation
            if not self._validate():
                raise InvalidTransactionSignature
        else:
            self.signature = sender_privkey.sign(self.payload, ec.ECDSA(hashes.SHA256()))

    @property
    def hash(self) -> bytes:
        """Calculate the hash of the transaction."""
        return hashlib.sha256(self.payload).digest()

    def __repr__(self) -> str:
        """Provide a user-friendly string for representation."""

        return (
            "Transaction("
            f"sender_pubkey={self.sender_pubkey.hex()[:8]}, "
            f"recipient={self.recipient.hex()[:8]}, "
            f"amount={self.amount}, fee={self.fee}, "
            f"signature={self.signature.hex()[:8]})"
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, type(self)) and self.payload == other.payload and self.signature == other.signature

    def to_dict(self) -> dict[str, Any]:
        """Return a view of the class as a dictionary."""

        result: dict[str, Any] = {}
        for f in fields(self):
            value = getattr(self, f.name)
            serializer = f.metadata.get("serialize", lambda x: x)  # pyright: ignore[reportUnknownLambdaType]
            result[f.name] = serializer(value)
        return result

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Self:
        """Convert a given dictionary into an instance of the class."""

        init_kwargs: dict[str, Any] = {}

        for f in fields(cls):
            value = d[f.name]
            deserializer = f.metadata.get("deserialize", lambda x: x)  # pyright: ignore[reportUnknownLambdaType]
            init_kwargs[f.name] = deserializer(value)
        return cls(**init_kwargs)

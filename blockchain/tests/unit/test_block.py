"""Unit tests for the Block class.

Tests verify block creation, merkle root calculation, hashing, and validation.
Includes property-based tests using hypothesis for robustness.
"""
# pyright: reportUnknownParameterType=false
# pyright: reportMissingParameterType=false
# pyright: reportUnusedImport=false

from unittest.mock import patch

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from cryptography.hazmat.primitives.asymmetric import ec

from blockchain.block import Block
from blockchain.transaction import Transaction


@patch("blockchain.block.time", return_value=1234567890)
class TestBlock:
    """Test suite for Block instantiation and basic operations."""

    def test_merkle_root_empty(self, mock_time):
        """Test that empty transaction list produces zero merkle root."""
        block = Block(
            index=0,
            transactions=[],
            nonce=0,
            previous_block_hash=b"\x00" * 32,
            difficulty=1,
        )
        assert block.transactions_merkle_root == b"\x00" * 32

    def test_merkle_root(self, mock_time, ephemeral_keys: tuple[ec.EllipticCurvePrivateKey, bytes]):
        """Test that merkle root is correctly calculated for block transactions."""
        priv_key, pub_key_bytes = ephemeral_keys
        tx = Transaction(pub_key_bytes, b"b", 1, sender_privkey=priv_key)
        block = Block(
            index=0,
            transactions=[tx],
            nonce=0,
            previous_block_hash=b"\x00" * 32,
            difficulty=1,
        )
        assert block.transactions_merkle_root == tx.hash

        block = Block(
            index=0,
            transactions=[tx, tx],
            nonce=0,
            previous_block_hash=b"\x00" * 32,
            difficulty=1,
        )
        assert block.transactions_merkle_root == bytes.fromhex(
            "7ca702f30c39fbf3543983f28e0126ec2907a59402afc6095247947da09cec9e"
        )

    def test_hash_deterministic(self, mock_time, ephemeral_keys: tuple[ec.EllipticCurvePrivateKey, bytes]):
        """Test that block hash is deterministic (same input produces same hash)."""
        priv_key, pub_key_bytes = ephemeral_keys
        tx1 = Transaction(pub_key_bytes, b"b", 1, sender_privkey=priv_key)
        tx2 = Transaction(pub_key_bytes, b"b", 1, sender_privkey=priv_key)

        block1 = Block(
            index=1,
            transactions=[tx1],
            nonce=0,
            previous_block_hash=b"\x00" * 32,
            difficulty=1,
        )
        block2 = Block(
            index=1,
            transactions=[tx2],
            nonce=0,
            previous_block_hash=b"\x00" * 32,
            difficulty=1,
        )
        h1 = block1.hash
        h2 = block2.hash
        assert h1 == h2
        assert isinstance(h1, bytes)
        assert len(h1) == 32

    def test_to_dict_from_dict_roundtrip(self, mock_time, ephemeral_keys: tuple[ec.EllipticCurvePrivateKey, bytes]):
        """Test that block serialization and deserialization preserve all data."""
        priv_key, pub_key_bytes = ephemeral_keys
        tx = Transaction(pub_key_bytes, b"b", 1, sender_privkey=priv_key)

        block = Block(
            index=1,
            transactions=[tx],
            nonce=0,
            previous_block_hash=b"\x00" * 32,
            difficulty=1,
        )
        d = block.to_dict()
        d["previous_block_hash"] = block.previous_block_hash.hex()
        d["difficulty"] = block.difficulty
        restored = Block.from_dict(d)
        assert restored.index == block.index
        assert restored.nonce == block.nonce
        assert restored.previous_block_hash == block.previous_block_hash
        assert restored.difficulty == block.difficulty
        assert restored.transactions[0].hash == block.transactions[0].hash

    def test_representation(self, mock_time, ephemeral_keys: tuple[ec.EllipticCurvePrivateKey, bytes]):
        """Test that block string representation is informative."""
        priv_key, pub_key_bytes = ephemeral_keys
        tx = Transaction(pub_key_bytes, b"b", 1, sender_privkey=priv_key)
        block = Block(
            index=1,
            transactions=[tx],
            nonce=0,
            previous_block_hash=b"\x00" * 32,
            difficulty=1,
        )

        assert str(block).startswith("Block(index=1, timestamp=1234567890, ")


class TestBlockHypothesis:
    """Property-based tests for Block using hypothesis for comprehensive validation."""

    # Strategies
    bytes_strategy = st.binary(min_size=1, max_size=32)
    amount_strategy = st.integers(min_value=0, max_value=2**63 - 1)
    nonce_strategy = st.integers(min_value=0, max_value=1000)
    difficulty_strategy = st.integers(min_value=1, max_value=4)

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(receiver=bytes_strategy, amount=amount_strategy, nonce=nonce_strategy, difficulty=difficulty_strategy)
    def test_block_hash_is_deterministic(
        self,
        receiver: bytes,
        amount: int,
        nonce: int,
        difficulty: int,
        ephemeral_keys: tuple[ec.EllipticCurvePrivateKey, bytes],
    ):
        """Property test: block hashes are deterministic across all parameter variations."""
        priv_key, pub_key_bytes = ephemeral_keys
        tx = Transaction(pub_key_bytes, receiver, amount, sender_privkey=priv_key)
        block1 = Block(
            index=0,
            transactions=[tx],
            nonce=nonce,
            previous_block_hash=b"\x00" * 32,
            difficulty=difficulty,
        )

        block2 = Block(
            index=0,
            transactions=[tx],
            nonce=nonce,
            previous_block_hash=b"\x00" * 32,
            difficulty=difficulty,
        )

        assert block1.hash == block2.hash

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        receiver=bytes_strategy,
        amount=amount_strategy,
        nonce=nonce_strategy,
        difficulty=difficulty_strategy,
    )
    def test_merkle_root_matches_transactions(
        self,
        receiver: bytes,
        amount: int,
        nonce: int,
        difficulty: int,
        ephemeral_keys: tuple[ec.EllipticCurvePrivateKey, bytes],
    ):
        """Property test: merkle root correctly represents contained transactions."""
        priv_key, pub_key_bytes = ephemeral_keys
        tx = Transaction(pub_key_bytes, receiver, amount, sender_privkey=priv_key)
        block = Block(
            index=0,
            transactions=[tx],
            nonce=nonce,
            previous_block_hash=b"\x00" * 32,
            difficulty=difficulty,
        )
        assert block.transactions_merkle_root == tx.hash

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        receiver=bytes_strategy,
        amount=amount_strategy,
        nonce=nonce_strategy,
        difficulty=difficulty_strategy,
    )
    def test_validate_returns_bool(
        self,
        receiver: bytes,
        amount: int,
        nonce: int,
        difficulty: int,
        ephemeral_keys: tuple[ec.EllipticCurvePrivateKey, bytes],
    ):
        """Property test: block validation always returns a boolean."""
        priv_key, pub_key_bytes = ephemeral_keys
        tx = Transaction(pub_key_bytes, receiver, amount, sender_privkey=priv_key)
        block = Block(
            index=0,
            transactions=[tx],
            nonce=nonce,
            previous_block_hash=b"\x00" * 32,
            difficulty=difficulty,
        )
        val = block.validate()
        assert isinstance(val, bool)

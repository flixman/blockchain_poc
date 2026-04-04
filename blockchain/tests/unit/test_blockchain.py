"""Unit tests for the Blockchain class.

Tests verify blockchain initialization, block addition, chain validation,
and serialization/deserialization capabilities.
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from blockchain.block import Block
from blockchain.blockchain import Blockchain
from blockchain.transaction import Transaction


@pytest.fixture
def initialized_bc() -> Blockchain:
    b = Block(0, [], 100, bytes(1), difficulty=1)
    genesis = Block.proof_of_work(last_block=b, transactions=[], difficulty=1)

    bc = Blockchain()
    bc.add_block(genesis)
    return bc


class TestBlockchain:
    """Test suite for Blockchain instantiation and operations."""

    def test_blockchain_initializes(self):
        """Test that blockchain initializes with an empty chain."""
        bc = Blockchain()
        assert len(bc) == 0

    def test_add_block_and_len(self, initialized_bc: Blockchain):
        """Test that blocks can be added to blockchain and length is updated."""
        bc = initialized_bc
        # Use empty sender and signature (reward transaction format)
        txs = [Transaction(b"", b"bob", 10)]
        block = Block(
            index=1,
            transactions=txs,
            nonce=0,
            previous_block_hash=bc.last_block.hash,
            difficulty=1,
        )
        bc.add_block(block)
        assert len(bc) == 2
        assert bc.last_block == block

    def test_chain_property_returns_list_of_blocks(self):
        """Test that chain property returns a list of Block objects."""
        bc = Blockchain()
        chain = bc.chain
        assert isinstance(chain, list)
        assert all(isinstance(b, Block) for b in chain)

    def test_set_replaces_chain(self, initialized_bc: Blockchain):
        """Test that set() method replaces the entire chain with another blockchain."""
        bc2 = initialized_bc
        # Use empty sender and signature (reward transaction format)
        txs = [Transaction(b"", b"bob", 10)]
        block = Block(
            index=1,
            transactions=txs,
            nonce=0,
            previous_block_hash=bc2.last_block.hash,
            difficulty=1,
        )
        bc2.add_block(block)

        bc1 = Blockchain()
        bc1.set(bc2)
        assert len(bc1) == len(bc2)
        assert bc1.last_block == bc2.last_block

    def test_validate_chain(self, initialized_bc: Blockchain):
        """Test that chain validation succeeds for valid chains and fails for corrupted chains."""
        bc = initialized_bc
        # Use empty sender and signature (reward transaction format)
        txs = [Transaction(b"", b"bob", 10)]
        block = Block.proof_of_work(
            last_block=bc.last_block,
            transactions=txs,
            difficulty=1,
        )
        bc.add_block(block)

        # Should be True for valid chain
        assert bc.validate()

        # Corrupt a block
        bc.chain[0].nonce += 1
        assert not bc.validate()

    @pytest.mark.security
    def test_chain_tamper_detection_via_hash_chain(self, initialized_bc: Blockchain):
        """Test that modifying a block invalidates chain due to hash link break."""
        bc = initialized_bc
        txs = [Transaction(b"", b"bob", 10)]
        block = Block.proof_of_work(
            last_block=bc.last_block,
            transactions=txs,
            difficulty=1,
        )
        bc.add_block(block)

        # Tamper with middle block by changing nonce
        original_nonce = bc.chain[0].nonce
        bc.chain[0].nonce += 1

        # Chain validation should fail
        assert not bc.validate()

        # Restore to confirm validation works
        bc.chain[0].nonce = original_nonce
        assert bc.validate()

    @pytest.mark.security
    def test_chain_integrity_broken_links_detected(self, initialized_bc: Blockchain):
        """Test that chain with broken links (wrong previous_block_hash) is rejected."""
        bc = initialized_bc
        txs = [Transaction(b"", b"bob", 10)]
        block = Block.proof_of_work(
            last_block=bc.last_block,
            transactions=txs,
            difficulty=1,
        )
        bc.add_block(block)

        # Corrupt the previous_block_hash link in second block
        original_hash = bc.chain[1].previous_block_hash
        bc.chain[1].previous_block_hash = b"\x00" * 32

        # Chain validation should fail
        assert not bc.validate()

        # Restore and confirm
        bc.chain[1].previous_block_hash = original_hash
        assert bc.validate()

    def test_serialize_deserialize_roundtrip(self, initialized_bc: Blockchain):
        """Test that blockchain can be serialized and deserialized without data loss."""
        bc = initialized_bc
        # Use empty sender and signature (reward transaction format)
        txs = [Transaction(b"", b"bob", 10)]
        block = Block.proof_of_work(
            last_block=bc.last_block,
            transactions=txs,
            difficulty=1,
        )
        bc.add_block(block)

        data = bc.serialize()
        bc_restored = Blockchain.deserialize(data)
        assert len(bc_restored) == len(bc)
        for b1, b2 in zip(bc.chain, bc_restored.chain):
            assert b1.index == b2.index
            assert b1.nonce == b2.nonce
            assert b1.previous_block_hash == b2.previous_block_hash
            assert b1.transactions_merkle_root == b2.transactions_merkle_root


# Property-based Hypothesis tests
class TestBlockchainHypothesis:
    """Property-based tests for Blockchain using hypothesis for robustness testing."""

    # Strategies
    bytes_strategy = st.binary(min_size=1, max_size=32)
    amount_strategy = st.integers(min_value=0, max_value=2**63 - 1)
    nonce_strategy = st.integers(min_value=0, max_value=1000)
    difficulty_strategy = st.integers(min_value=1, max_value=2)

    @given(
        sender=bytes_strategy,
        recipient=bytes_strategy,
        amount=amount_strategy,
        difficulty=difficulty_strategy,
    )
    def test_add_block_and_validate(
        self,
        sender: bytes,
        recipient: bytes,
        amount: int,
        difficulty: int,
    ):
        """Property test: blocks can be added and validated across parameter variations."""
        bc = Blockchain()
        prev_block = Block(0, [], 100, bytes(1), difficulty=1)
        # Use empty sender and signature for testing (reward transaction format)
        txs = [Transaction(b"", recipient, amount)]
        block = Block.proof_of_work(
            last_block=prev_block,
            transactions=txs,
            difficulty=difficulty,
        )

        bc.add_block(block)
        assert bc.validate()
        assert bc.last_block == block

    @given(sender=bytes_strategy, recipient=bytes_strategy, amount=amount_strategy)
    def test_serialize_deserialize_roundtrip(
        self,
        sender: bytes,
        recipient: bytes,
        amount: int,
    ):
        """Property test: serialization roundtrip preserves blockchain integrity."""
        bc = Blockchain()
        prev_block = Block(0, [], 100, bytes(1), difficulty=1)
        # Use empty sender and signature for testing (reward transaction format)
        txs = [Transaction(b"", recipient, amount)]
        block = Block.proof_of_work(
            last_block=prev_block,
            transactions=txs,
            difficulty=1,
        )
        bc.add_block(block)

        data = bc.serialize()
        bc_restored = Blockchain.deserialize(data)
        assert len(bc_restored) == len(bc)
        for b1, b2 in zip(bc.chain, bc_restored.chain):
            assert b1.transactions_merkle_root == b2.transactions_merkle_root

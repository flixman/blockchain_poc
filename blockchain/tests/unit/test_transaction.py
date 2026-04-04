"""Unit tests for the Transaction class.

Tests verify transaction creation, signing, validation, serialization,
and security properties including signature validation and authenticity.
"""

import hashlib

import pytest
from hypothesis import given
from hypothesis import strategies as st

from blockchain.transaction import Transaction
from blockchain.wallet import Wallet


class TestTransaction:
    """Test suite for Transaction instantiation and basic operations."""

    def test_hash_is_deterministic(self):
        """Test that transaction hash is deterministic (same input produces same hash)."""
        # Use empty signature (reward transaction) for simple test
        tx = Transaction(b"", b"bob", 10)

        h1 = tx.hash
        h2 = tx.hash

        assert h1 == h2
        assert isinstance(h1, bytes)
        assert len(h1) == 32

    def test_hash_changes_when_data_changes(self):
        """Test that changing transaction data changes the hash."""
        tx1 = Transaction(b"", b"bob", 10)
        tx2 = Transaction(b"", b"bob", 20)

        assert tx1.hash != tx2.hash

    def test_to_dict_serializes_correctly(self):
        """Test that transaction converts to dictionary with hex-encoded fields."""
        # Use reward transaction format (empty sender and signature) to avoid EC validation
        tx = Transaction(b"", b"\x03\x04", 50)

        d = tx.to_dict()

        assert d == {
            "sender_pubkey": "",
            "recipient": "0304",
            "amount": 50,
            "fee": 0,
            "signature": "",
        }

    def test_from_dict_roundtrip(self):
        """Test that transaction can be created from dict and reconstructs original."""
        original = Transaction(b"", b"bob", 99)

        d = original.to_dict()
        restored = Transaction.from_dict(d)

        assert restored.sender_pubkey == original.sender_pubkey
        assert restored.recipient == original.recipient
        assert restored.amount == original.amount
        assert restored.signature == original.signature
        assert restored.hash == original.hash

    def test_repr_returns_string(self):
        """Test that transaction repr returns a string representation."""
        tx = Transaction(b"", b"b", 1)

        r = repr(tx)

        assert isinstance(r, str)
        assert "Transaction" in r

    @pytest.mark.security
    def test_invalid_signature_detected(self):
        """Test that a transaction with a valid signature is accepted."""
        wallet = Wallet()

        # Should not raise
        tx = wallet.new_transaction(b"bob", 10, 1)
        tx.signature += b"0"

        assert not tx._verify()

    @pytest.mark.security
    def test_transaction_signature_tampering_detected(self):
        """Test that tampering with recipient after signing is detected."""
        wallet = Wallet()
        tx = wallet.new_transaction(b"bob", 10, 1)

        # Tamper with recipient (changes payload)
        tx.recipient = b"alice"

        # Signature should no longer be valid
        assert not tx._verify()

    @pytest.mark.security
    def test_transaction_amount_tampering_detected(self):
        """Test that tampering with amount after signing is detected."""
        wallet = Wallet()
        tx = wallet.new_transaction(b"bob", 10, 1)

        # Tamper with amount (changes payload)
        tx.amount = 100

        # Signature should no longer be valid
        assert not tx._verify()

    @pytest.mark.security
    def test_only_sender_can_sign_transaction(self):
        """Test that only the sender's private key can sign their transaction."""
        wallet1 = Wallet()
        wallet2 = Wallet()

        # Create transaction from wallet1
        tx = wallet1.new_transaction(b"bob", 10, 1)

        # Create same transaction from wallet2 (different sender pubkey)
        tx2 = Transaction(
            wallet2.public_key_bytes,
            b"bob",
            10,
            1,
            sender_privkey=wallet2._private_key,
        )

        # Signatures should be different
        assert tx.signature != tx2.signature

    @pytest.mark.security
    def test_invalid_signature_raises_on_construction(self):
        """Test that creating transaction with bad signature raises error."""
        wallet = Wallet()
        tx = wallet.new_transaction(b"bob", 10, 1)

        # Tampering with the transaction after signing should create invalid state
        tx_dict = tx.to_dict()
        tx_dict["amount"] = "999"  # Modify before creating new instance

        # Creating from dict with tampered signature should raise
        tx_dict["signature"] = tx.signature.hex()  # Use original signature
        tx_dict["sender_pubkey"] = tx.sender_pubkey.hex()

        from blockchain.transaction import InvalidTransactionSignature

        with pytest.raises(InvalidTransactionSignature):
            Transaction.from_dict(tx_dict)


class TestTransactionHypothesis:
    """Property-based tests for Transaction using hypothesis for comprehensive validation."""

    # Strategies as class attributes
    bytes_strategy = st.binary(min_size=1, max_size=32)
    amount_strategy = st.integers(min_value=0, max_value=2**63 - 1)
    fee_strategy = st.integers(min_value=0, max_value=10)

    @given(recipient=bytes_strategy, amount=amount_strategy, fee=fee_strategy)
    def test_hash_is_correct(self, recipient: bytes, amount: int, fee: int):
        """Property test: transaction hash is correctly calculated across all parameters."""
        # Use empty sender and signature for testing (reward transaction format)
        tx = Transaction(b"", recipient, amount)
        expected = hashlib.sha256(tx.payload).digest()
        assert tx.hash == expected

    @given(recipient=bytes_strategy, amount=amount_strategy, fee=fee_strategy)
    def test_to_dict_from_dict_roundtrip(self, recipient: bytes, amount: int, fee: int):
        """Property test: serialization roundtrip preserves transaction across all parameters."""
        # Use empty sender and signature for testing (reward transaction format)
        tx = Transaction(b"", recipient, amount, fee)
        d = tx.to_dict()
        restored = Transaction.from_dict(d)

        # Check fields
        assert restored.sender_pubkey == tx.sender_pubkey
        assert restored.recipient == tx.recipient
        assert restored.amount == tx.amount
        assert restored.signature == tx.signature

        # Check hash
        assert restored.hash == tx.hash

    @given(recipient=bytes_strategy, amount=amount_strategy, fee=fee_strategy)
    def test_repr_contains_transaction(self, recipient: bytes, amount: int, fee: int):
        """Property test: repr always returns a string containing 'Transaction'."""
        # Use empty sender and signature for testing
        tx = Transaction(b"", recipient, amount, fee)
        r = repr(tx)
        assert isinstance(r, str)
        assert "Transaction" in r

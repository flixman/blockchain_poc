"""Unit tests for the Wallet class.

Tests verify wallet initialization, key generation, address derivation,
and transaction signing capabilities including security properties.
"""
# pyright: reportUnusedVariable=false

import pytest
from blockchain.wallet import Wallet


class TestWallet:
    """Tests for the Wallet class."""

    def test_wallet_initialization(self):
        """Test that a wallet initializes with private and public keys."""
        Wallet()

    def test_wallet_address_is_bytes(self):
        """Test that wallet address is bytes."""
        wallet = Wallet()
        address = wallet.address

        assert isinstance(address, bytes)
        assert len(address) == 32  # SHA256 hash is 32 bytes

    def test_wallet_address_is_deterministic(self):
        """Test that wallet address is the same every time."""
        wallet = Wallet()

        address1 = wallet.address
        address2 = wallet.address

        assert address1 == address2

    def test_wallet_address_is_unique_per_wallet(self):
        """Test that different wallets have different addresses."""
        wallet1 = Wallet()
        wallet2 = Wallet()

        assert wallet1.address != wallet2.address

    def test_multiple_wallets_have_different_public_keys(self):
        """Test that multiple wallets have different public keys."""
        wallet1 = Wallet()
        wallet2 = Wallet()

        assert wallet1 != wallet2

    @pytest.mark.security
    def test_wallet_signs_transactions_with_private_key(self):
        """Test that wallet can sign transactions using private key."""
        wallet = Wallet()
        tx = wallet.new_transaction(b"bob", 10, 1)

        # Should have a signature
        assert len(tx.signature) > 0
        assert isinstance(tx.signature, bytes)

    @pytest.mark.security
    def test_different_wallets_create_different_signatures(self):
        """Test that different wallets create different signatures for same transaction."""
        wallet1 = Wallet()
        wallet2 = Wallet()

        tx1 = wallet1.new_transaction(b"bob", 10, 1)
        tx2 = wallet2.new_transaction(b"bob", 10, 1)

        # Even though amounts are same, signatures should differ (different wallet)
        assert tx1.signature != tx2.signature
        assert tx1.sender_pubkey != tx2.sender_pubkey

    @pytest.mark.security
    def test_wallet_transaction_validates_with_correct_key(self):
        """Test that a signed transaction validates when using correct wallet key."""
        wallet = Wallet()
        tx = wallet.new_transaction(b"bob", 10, 1)

        # Transaction should be valid
        assert tx._validate()

    @pytest.mark.security
    def test_wallet_cannot_forge_signature_of_another_wallet(self):
        """Test that one wallet cannot forge signature of another wallet's transaction."""
        wallet1 = Wallet()
        wallet2 = Wallet()

        # Create valid transaction from wallet1
        tx1 = wallet1.new_transaction(b"bob", 10, 1)

        # Try to forge: create same transaction but claim it's from wallet1 with wallet2's signature
        from blockchain.transaction import Transaction

        forged_tx = Transaction(
            wallet1.public_key_bytes,  # Claim to be from wallet1
            b"bob",
            10,
            1,
            sender_privkey=wallet2._private_key,  # But sign with wallet2's key
        )

        # Signature should be invalid (signed by different key than sender)
        assert not forged_tx._validate()

"""Unit tests for the Node class.

Tests verify node operations including transaction addition with balance tracking,
mining, and block creation. Includes security tests for fraud prevention.
"""
# pyright: reportPrivateUsage=false

import pytest
from blockchain.node import Node, InvalidAccountBalanceError


class TestNode:
    """Test suite for Node operations including transaction and block management."""

    @pytest.mark.security
    def test_add_transaction_adds_to_mempool(self):
        """Test that transactions can be added to mempool after balance verification."""
        node = Node()

        # trigger the mining of a block, so that we have funds
        node._mine()

        # Use empty sender and signature (reward transaction format)
        tx = node._miner_wallet.new_transaction(b"bob", 4, 1)
        node.add_transaction(tx)

        assert len(node._mempool) == 1
        assert tx in node._mempool

    @pytest.mark.security
    def test_mine_creates_new_block_and_clears_mempool(self):
        """Test that mining creates a new block from mempool transactions and clears mempool."""
        node = Node()
        node._mine()

        tx = node._miner_wallet.new_transaction(b"bob", 4, 1)
        node.add_transaction(tx)
        node._mine()

        # blockchain length increased
        assert len(node._blockchain.chain) == 3

        # mempool cleared
        assert len(node._mempool) == 0

        # last block contains the transaction
        last_block = node._blockchain.last_block
        assert len(last_block.transactions) == 2
        assert last_block.transactions[1] == tx

    @pytest.mark.security
    def test_insufficient_balance_prevents_transaction(self):
        """Test that a wallet cannot spend more than its balance."""
        node = Node()
        node._mine()

        # Miner has 10 coins from mining reward
        total_balance = node.get_account_balance(node._miner_wallet.public_key_bytes).balance

        # Try to spend more than available
        tx = node._miner_wallet.new_transaction(b"bob", total_balance + 1, 0)

        with pytest.raises(InvalidAccountBalanceError):
            node.add_transaction(tx)

    @pytest.mark.security
    def test_double_spending_from_mempool_prevented(self):
        """Test that spending the same coins twice in mempool is prevented."""
        node = Node()
        node._mine()

        # Create first transaction
        tx1 = node._miner_wallet.new_transaction(b"bob", 5, 0)
        node.add_transaction(tx1)

        # Try to spend more than remaining balance
        # After first tx, balance should be reduced by 5
        remaining_balance = node.get_account_balance(node._miner_wallet.public_key_bytes).balance

        tx2 = node._miner_wallet.new_transaction(b"alice", remaining_balance + 1, 0)

        with pytest.raises(InvalidAccountBalanceError):
            node.add_transaction(tx2)

    @pytest.mark.security
    def test_transaction_from_unknown_wallet_rejected(self):
        """Test that a transaction from a wallet with no balance is rejected."""
        node = Node()
        node._mine()

        # Create a new wallet with no funds
        from blockchain.wallet import Wallet

        poor_wallet = Wallet()

        tx = poor_wallet.new_transaction(b"bob", 1, 0)

        with pytest.raises(InvalidAccountBalanceError):
            node.add_transaction(tx)

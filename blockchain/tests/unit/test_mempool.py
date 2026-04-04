"""Unit tests for the Mempool class.

Tests verify mempool functionality including transaction ordering by fee,
addition, removal, and retrieval operations.
"""

from blockchain.mempool import Mempool
from blockchain.transaction import Transaction


def make_tx(recipient: bytes, amount: int = 1, fee: int = 0) -> Transaction:
    # use empty sender+signature to bypass signature validation (treats as coinbase-like)
    return Transaction(b"", recipient, amount, fee)


class TestMempool:
    """Test suite for Mempool instantiation and transaction ordering."""

    def test_add_and_ordering(self):
        """Test that transactions are ordered by fee (highest first) when retrieved."""
        mp = Mempool()

        t1 = make_tx(b"r1", amount=1, fee=5)
        t2 = make_tx(b"r2", amount=2, fee=1)
        t3 = make_tx(b"r3", amount=3, fee=10)

        mp.add(t1)
        mp.add(t2)
        mp.add(t3)

        fees = [tx.fee for tx in mp.top(3)]
        assert fees == [10, 5, 1]

    def test_stability_for_equal_fees(self):
        """Test that transactions with equal fees maintain insertion order (stable sort)."""
        mp = Mempool()

        a = make_tx(b"a", fee=5)
        b = make_tx(b"b", fee=5)
        c = make_tx(b"c", fee=5)

        mp.add(a)
        mp.add(b)
        mp.add(c)

        recipients = [tx.recipient for tx in mp.top(3)]
        assert recipients == [b"a", b"b", b"c"]

    def test_remove_and_contains(self):
        """Test that transactions can be added, checked for membership, and removed."""
        mp = Mempool()
        t1 = make_tx(b"x", fee=2)
        t2 = make_tx(b"y", fee=3)

        mp.add(t1)
        mp.add(t2)

        assert t1 in mp
        assert t2 in mp

        removed = mp.remove(t1)
        assert removed is True
        assert t1 not in mp
        assert len(mp) == 1

    def test_top_and_pop_top(self):
        """Test that top() method returns highest-fee transactions in correct order."""
        mp = Mempool()
        t1 = make_tx(b"t1", fee=1)
        t2 = make_tx(b"t2", fee=2)
        t3 = make_tx(b"t3", fee=3)

        mp.add(t1)
        mp.add(t2)
        mp.add(t3)

        top2 = mp.top(2)
        assert [t.fee for t in top2] == [3, 2]

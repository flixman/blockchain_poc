"""Module for mempool definition and operations."""

from bisect import insort
from itertools import count

from blockchain.transaction import Transaction


class Mempool:
    """
    A sorted mempool keyed by transaction hash.

    - Keeps a sorted list of entries (neg_fee, seq, tx_hash) so highest-fee is first.
    - Keeps a dict mapping tx_hash -> Transaction for O(1) lookup/removal.
    """

    def __init__(self) -> None:
        """Initialize a new instance of the class."""
        # list of tuples (neg_fee, seq, tx_hash) so that list is ascending and highest fee is at index 0
        self._items: list[tuple[int, int, bytes]] = []
        self._by_hash: dict[bytes, Transaction] = {}
        self._seq = count()

    def add(self, tx: Transaction) -> None:
        """
        Add a transaction to the mempool.

        Transactions are ordered by fee (highest first) for mining priority.
        Duplicate transactions (same hash) are ignored.

        Args:
            tx: Transaction to add to the mempool.

        """
        key = tx.hash
        if key in self._by_hash:
            # Transaction hash already present — model guarantees immutability
            # (fee and contents cannot change), so treat as a no-op.
            return
        insort(self._items, (-int(tx.fee), next(self._seq), key))
        self._by_hash[key] = tx

    def remove(self, tx: Transaction) -> bool:
        """
        Remove a transaction from the mempool.

        Args:
            tx: Transaction to remove.

        Returns:
            bool: True if transaction was removed, False if not found.

        """
        return self._remove_by_hash(tx.hash)

    def _remove_by_hash(self, key: bytes) -> bool:
        if key not in self._by_hash:
            return False
        # find and remove from sorted list
        for i, (_, _, h) in enumerate(self._items):
            if h == key:
                del self._items[i]
                break
        del self._by_hash[key]
        return True

    def top(self, n: int = 1) -> list[Transaction]:
        """
        Retrieve the top n transactions by fee.

        Args:
            n: Number of transactions to retrieve (default: 1).

        Returns:
            List[Transaction]: Transactions sorted by fee (highest first).

        """
        return [self._by_hash[h] for _, _, h in self._items[:n]]

    def __len__(self) -> int:
        """Return the amount of transactions in the pool."""
        return len(self._items)

    def __contains__(self, tx: Transaction) -> bool:
        """Return if the given transactions is already in the pool or not."""
        return tx.hash in self._by_hash

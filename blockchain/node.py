from uuid import uuid4

from blockchain.account_balance import AccountBalance
from blockchain.block import Block
from blockchain.blockchain import Blockchain
from blockchain.mempool import Mempool
from blockchain.wallet import Wallet
from blockchain.transaction import Transaction


_FIXED_REWARD = 100


class InvalidAccountBalance(Exception):
    """Exception raised when a transaction is invalid due to insufficient balances"""


class Node:
    """Model a blockchain node server."""

    def __init__(self) -> None:
        """Initialize the Node Server instance."""
        self._account_balances: dict[bytes, AccountBalance] = {}
        self._id: str = str(uuid4()).replace("-", "")
        self._mempool: Mempool = Mempool()
        self._blockchain = Blockchain()
        self._difficulty: int = 4
        self._miner_wallet: Wallet = Wallet()

        prev_block = Block(0, [], 100, bytes(1), difficulty=1)
        genesis_block = Block.proof_of_work(
            last_block=prev_block,
            transactions=[],
            difficulty=self._difficulty,
        )
        self._blockchain.add_block(genesis_block)

    def add_transaction(self, tx: Transaction) -> None:
        """Add a transaction to the mempool."""
        sender_wallet = self.get_account_balance(tx.sender_pubkey)
        recipient_wallet = self.get_account_balance(tx.recipient)

        total = tx.amount + tx.fee
        # CHALLENGE: prevent unauthorized minting
        # if sender_wallet.balance < total:
        #     raise InvalidAccountBalance(f"Insufficient funds: {sender_wallet.balance} < {total}")

        sender_wallet.balance -= total
        recipient_wallet.balance += tx.amount

        self._mempool.add(tx)

    def _mine(self) -> None:
        """Create a block out of the mempool transactions."""

        select_transactions = self._mempool.top(10)

        reward = _FIXED_REWARD + sum(x.fee for x in select_transactions)
        coinbase = Transaction(b"", self._miner_wallet.address, reward, 0)

        select_transactions = [coinbase] + select_transactions

        block = Block.proof_of_work(
            last_block=self._blockchain.last_block, transactions=select_transactions, difficulty=self._difficulty
        )

        self._blockchain.add_block(block)

        sender_wallet = self.get_account_balance(self._miner_wallet.public_key_bytes)
        sender_wallet.balance += reward

        for tx in select_transactions:
            self._mempool.remove(tx)

    def get_account_balance(self, pubkey: bytes) -> AccountBalance:
        try:
            return self._account_balances[pubkey]
        except KeyError:
            return self._account_balances.setdefault(pubkey, AccountBalance(pubkey, 0))

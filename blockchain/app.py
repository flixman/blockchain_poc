"""Module for node server definition and operations."""

import logging
import sys

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from blockchain.node import Node, InvalidAccountBalance
from blockchain.transaction import InvalidTransactionSignature, Transaction


logging.basicConfig(stream=sys.stderr, level=logging.INFO)

logger = logging.getLogger("Node")


class TransactionModel(BaseModel):
    """Pydantic class to model a transaction."""

    sender_pubkey: str
    recipient: str
    amount: int
    fee: int
    signature: str

    def get_transaction(self) -> Transaction:
        """Convert the Pydantic model to a Transaction instance.

        Returns:
            Transaction: Transaction object created from this model's fields.
        """
        return Transaction(
            sender_pubkey=bytes.fromhex(self.sender_pubkey),
            recipient=bytes.fromhex(self.recipient),
            amount=self.amount,
            fee=self.fee,
            signature=bytes.fromhex(self.signature),
        )


def create_app(node: Node | None = None) -> FastAPI:
    """Create the FastAPI app."""
    app = FastAPI()
    _node = node or Node()

    @app.post("/transactions/new", status_code=status.HTTP_201_CREATED)
    async def new_tx(tx: TransactionModel) -> None:  # pyright: ignore[reportUnusedFunction]
        """Receive a new transaction to append to the mempool."""
        try:
            txn = tx.get_transaction()
            logger.info("Received transaction: %s", txn)
            # CHALLENGE: prevent miner impersonation
            # if txn.sender_pubkey == b"" and txn.signature == b"":
            #     raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="External miner reward")
            _node.add_transaction(txn)
        except InvalidTransactionSignature:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid transaction signature")
        except InvalidAccountBalance:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Insufficient funds")

    @app.get("/blocks", status_code=status.HTTP_200_OK)
    async def get_blocks() -> list[dict[str, object]]:  # pyright: ignore[reportUnusedFunction] # pragma: nocover
        """Return the blockchain as JSON-serializable block data."""
        return [block.to_dict() for block in _node._blockchain.chain]

    @app.post("/wallets/{pubkey}/topup", status_code=status.HTTP_200_OK)
    async def top_up_wallet(pubkey: str) -> None:  # pyright: ignore[reportUnusedFunction] # pragma: nocover
        """Put money on the wallet, mining a block for it if required"""

        try:
            pubkey_bytes = bytes.fromhex(pubkey)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid public key")

        if _node.get_account_balance(_node._miner_wallet.public_key_bytes).balance < 10:
            _node._mine()
        txn = Transaction(
            _node._miner_wallet.public_key_bytes, pubkey_bytes, 10, 0, sender_privkey=_node._miner_wallet._private_key
        )
        _node.add_transaction(txn)
        _node._mine()
        logger.info("Startup money: %s", txn)

    @app.get("/wallets/{pubkey}/balance", status_code=status.HTTP_200_OK)
    async def get_wallet_balance(pubkey: str) -> dict[str, int | str]:  # pyright: ignore[reportUnusedFunction] # pragma: nocover
        """Return the current balance for the wallet identified by its public key."""
        try:
            pubkey_bytes = bytes.fromhex(pubkey)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid public key")

        balance = _node.get_account_balance(pubkey_bytes).balance
        return {"balance": balance}

    return app

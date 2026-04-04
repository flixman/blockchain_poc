# pyright: reportPrivateUsage=false

from fastapi.testclient import TestClient
from fastapi import status

from blockchain.node import Node
from blockchain.app import create_app


class TestApp:
    def test_add_transaction(self):
        """Test adding a transaction with valid signature."""
        node = Node()
        client = TestClient(create_app(node))

        # trigger the mining of a block, so that we have funds
        node._mine()

        # Create a wallet and sign a transaction
        recipient = b"bob"
        amount = 3
        fee = 1

        new_transaction = node._miner_wallet.new_transaction(recipient, amount, fee)

        response = client.post("/transactions/new", json=new_transaction.to_dict())

        assert response.status_code == status.HTTP_201_CREATED
        assert len(node._mempool) == 1

"""Unit tests for the FastAPI application.

Tests verify API endpoints including transaction creation and validation,
with security focus on rejecting invalid signatures and malformed requests.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import status
from cryptography.hazmat.primitives.asymmetric import ec
from unittest.mock import patch, MagicMock

from blockchain.app import create_app
from blockchain.transaction import Transaction


@pytest.fixture
@patch("blockchain.app.Node")
def client_node(mock_node: MagicMock) -> tuple[TestClient, MagicMock]:
    # Create the FastAPI app instance using the factory function
    app = create_app()

    # Create a TestClient for the FastAPI app
    return TestClient(app), mock_node


class TestApp:
    """Test suite for FastAPI application endpoints."""

    def test_new_transaction(
        self, client_node: tuple[TestClient, MagicMock], ephemeral_keys: tuple[ec.EllipticCurvePrivateKey, bytes]
    ):
        """Test that valid transactions can be posted to the API endpoint."""
        client, node = client_node
        priv_key, pub_key_bytes = ephemeral_keys
        new_transaction = Transaction(pub_key_bytes, b"b", 1, sender_privkey=priv_key)

        response = client.post("/transactions/new", json=new_transaction.to_dict())
        assert response.status_code == status.HTTP_201_CREATED

        # Verify that the mocked Node's add_transaction method was called
        node.return_value.add_transaction.assert_called_once()

    @pytest.mark.security
    def test_invalid_signature(
        self, client_node: tuple[TestClient, MagicMock], ephemeral_keys: tuple[ec.EllipticCurvePrivateKey, bytes]
    ):
        """Test that API rejects transactions with invalid signatures."""
        client, _ = client_node
        priv_key, pub_key_bytes = ephemeral_keys
        new_transaction = Transaction(pub_key_bytes, b"b", 1, sender_privkey=priv_key)
        new_transaction.signature += b"0"

        response = client.post("/transactions/new", json=new_transaction.to_dict())
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization


@pytest.fixture
def ephemeral_keys() -> tuple[ec.EllipticCurvePrivateKey, bytes]:
    private_value = int.from_bytes(b"123456")

    # Create private key from a deterministic value
    private_key = ec.derive_private_key(private_value, ec.SECP256K1(), default_backend())
    public_key_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )

    return private_key, public_key_bytes

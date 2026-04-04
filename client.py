"""Simple command-line client for the blockchain API."""

from __future__ import annotations

import argparse
from pathlib import Path
import logging
import sys
import textwrap

import requests
import pandas as pd
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from blockchain.transaction import Transaction


DEFAULT_SERVER = "http://127.0.0.1:8000"

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger("client")


def _load_or_create_wallet(path: Path) -> tuple[ec.EllipticCurvePrivateKey, bytes]:
    if path.exists():
        private_key = serialization.load_pem_private_key(path.read_bytes(), password=None)
        if not isinstance(private_key, ec.EllipticCurvePrivateKey):
            raise TypeError(f"Expected an EC private key in {path}")
    else:
        private_key = ec.generate_private_key(ec.SECP256K1())
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        path.write_bytes(pem)

    public_key_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )

    return private_key, public_key_bytes


def _post_transaction(server: str, transaction: Transaction) -> None:
    response = requests.post(f"{server}/transactions/new", json=transaction.to_dict(), timeout=10)
    if response.status_code != 201:
        logger.error(f"transaction rejected: %s", response.text)
        sys.exit(1)
    logger.info("transaction accepted")


def _show_blocks(server: str) -> None:
    response = requests.get(f"{server}/blocks", timeout=10)
    response.raise_for_status()
    blocks = response.json()

    for block in blocks:
        transactions = []
        for tx in block["transactions"]:
            transactions.append(
                {
                    "sender_pubkey": tx["sender_pubkey"][:8],
                    "recipient": tx["recipient"][:8],
                    "amount": tx["amount"],
                    "fee": tx["fee"],
                    "signature": tx["signature"][:8],
                }
            )

        table = pd.DataFrame(transactions, columns=["sender_pubkey", "recipient", "amount", "fee", "signature"])
        block_summary = textwrap.indent(
            (
                f"\nblock index: {block['index']}\n"
                f"timestamp: {block['timestamp']}\n"
                f"nonce: {block['nonce']}\n"
                f"difficulty: {block['difficulty']}\n"
                f"previous_block_hash: {block['previous_block_hash'][:8]}\n"
                f"{table.to_string(index=False) if not table.empty else '<no transactions>'}"
            ),
            "    ",
        )
        logger.info("%s", block_summary)


def _show_balance(server: str, public_key_hex: str) -> None:
    response = requests.get(f"{server}/wallets/{public_key_hex}/balance", timeout=10)
    response.raise_for_status()
    data = response.json()
    logger.info("balance: %s", data["balance"])


def _topup_wallet(server: str, public_key_hex: str) -> None:
    response = requests.post(f"{server}/wallets/{public_key_hex}/topup", timeout=10)
    response.raise_for_status()


if __name__ == "__main__":  # pragma: no cover
    """Parse commands and interact with the blockchain API."""
    parser = argparse.ArgumentParser(description="Interact with the blockchain API.")
    parser.add_argument("--server", default=DEFAULT_SERVER, help="Base URL of the blockchain API")
    parser.add_argument("--wallet-file", default="wallet.pem", help="Path to the wallet PEM file")

    subparsers = parser.add_subparsers(dest="command", required=True)

    wallet_init_parser = subparsers.add_parser("init-wallet", help="Generate a new wallet file")
    wallet_show_parser = subparsers.add_parser("show-wallet", help="Show the content of the wallet")
    wallet_topup_parser = subparsers.add_parser("topup-wallet", help="Request money into the wallet")

    send_parser = subparsers.add_parser("send", help="Create and submit a signed transaction")
    send_parser.add_argument("--recipient", required=True, help="Recipient label to encode into the transaction")
    send_parser.add_argument("--amount", type=int, required=True, help="Amount to transfer")
    send_parser.add_argument("--fee", type=int, default=0, help="Transaction fee")

    subparsers.add_parser("blocks", help="Fetch and display the blockchain")

    args = parser.parse_args()

    if args.command == "init-wallet":
        if Path(args.wallet_file).exists():
            raise SystemExit(f"wallet file already exists: {args.wallet_file}")

        private_key, public_key_bytes = _load_or_create_wallet(Path(args.wallet_file))
        logger.info("saved wallet to %s", args.wallet_file)
        logger.info("public key: %s", public_key_bytes.hex()[:8])
    elif args.command == "show-wallet":
        private_key, public_key_bytes = _load_or_create_wallet(Path(args.wallet_file))
        logger.info("public key: %s", public_key_bytes.hex()[:8])
        _show_balance(args.server, public_key_bytes.hex())
    elif args.command == "topup-wallet":
        private_key, public_key_bytes = _load_or_create_wallet(Path(args.wallet_file))
        _topup_wallet(args.server, public_key_bytes.hex())
    elif args.command == "send":
        private_key, public_key_bytes = _load_or_create_wallet(Path(args.wallet_file))
        transaction = Transaction(
            sender_pubkey=public_key_bytes,
            recipient=args.recipient.encode(),
            amount=args.amount,
            fee=args.fee,
            sender_privkey=private_key,
        )
        _post_transaction(args.server, transaction)
    elif args.command == "blocks":
        _show_blocks(args.server)

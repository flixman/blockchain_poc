"""Module for account balance definition and operations."""

from dataclasses import dataclass


@dataclass
class AccountBalance:
    """
    Track the balance of an account identified by its public key.

    Attributes:
        pubkey: The account's public key (bytes).
        balance: Current account balance (default: 0).

    """

    pubkey: bytes
    balance: int = 0

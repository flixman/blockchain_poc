# Blockchain Proof of Concept

A simple blockchain implementation in Python to showcase fundamental blockchain concepts and security properties. This is a **proof-of-concept implementation** for educational purposes and experimentation with blockchain mechanics:

- **Not production-ready**: Use only for learning about blockchain mechanics
- **Consensus model**: Simple proof-of-work (not Byzantine Fault Tolerant)
- **Network**: Single-node (no peer-to-peer networking)
- **Cryptography**: Well-tested libraries (cryptography, hashlib)
- **Performance**: Optimized for clarity, not high throughput

## Features

- **Block Structure**: Immutable blocks with merkle root validation
- **Transaction Management**: Signed transactions with cryptographic verification
- **Blockchain Validation**: Chain integrity verification with proof-of-work consensus
- **Wallet System**: Elliptic curve cryptography (SECP256K1) for secure transaction signing
- **Mempool**: Transaction pool with fee-based ordering
- **Node Implementation**: Full node with mining capabilities and balance tracking
- **FastAPI Server**: REST API for transaction submission and blockchain queries

## Security Features

- **Digital Signatures**: All transactions must be cryptographically signed by the sender
- **Merkle Tree Verification**: Transaction integrity via merkle root hashing
- **Proof of Work**: Adjustable difficulty consensus mechanism
- **Balance Validation**: Double-spending prevention through account balance tracking
- **Signature Verification**: Invalid signatures are rejected at both transaction and API levels
- **Chain Integrity**: Tampering detection through linked block hashing

## Project Structure

```
blockchain/
├── account_balance.py      # Account balance tracking
├── app.py                  # FastAPI application
├── block.py                # Block definition and operations
├── blockchain.py           # Blockchain management
├── mempool.py              # Transaction mempool with fee ordering
├── node.py                 # Node operations and mining
├── transaction.py          # Transaction definition and signing
├── wallet.py               # Wallet and key management
└── tests/                  # Comprehensive test suite
    ├── conftest.py         # Pytest fixtures
    ├── unit/               # Unit tests
    │   ├── test_app.py     # API endpoint tests
    │   ├── test_block.py   # Block tests (unit + property-based)
    │   ├── test_blockchain.py  # Blockchain tests (unit + property-based)
    │   ├── test_mempool.py # Mempool tests
    │   ├── test_node.py    # Node tests (including fraud prevention)
    │   ├── test_transaction.py # Transaction tests (unit + property-based)
    │   └── test_wallet.py  # Wallet and signing tests
    └── integration/        # Integration tests
        └── test_app.py     # Full application tests
```

## Development Environment

This project uses **Dev Containers** for a consistent, reproducible development environment.

### Using Dev Containers

Dev Containers provide a containerized development environment with all dependencies pre-configured:

1. **Install prerequisites**:
   - [Docker](https://docs.docker.com/get-docker/)
   - [VS Code](https://code.visualstudio.com/) with [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

2. **Open in container**:
   - Clone the repository
   - Open in VS Code
   - Click the "Reopen in Container" prompt, or use the command palette (`Ctrl+Shift+P`) and select "Dev Containers: Reopen in Container"

3. **Ready to go**:
   - All dependencies are automatically installed
   - Python environment is pre-configured
   - Start developing immediately

For more details, see the [devcontainer configuration](./devcontainer/Containerfile).

## Running the Application

### Start the node server

```bash
python server.py
```

The API will be available at `http://localhost:8000`

### Use the client

Generate a wallet file:

```bash
python client.py --wallet-file wallet.pem init-wallet
```

Request the miner to give you an allowance:

```bash
python client.py --wallet-file wallet.pem topup-wallet
```

Retrieve and display the current wallet balance:

```bash
python client.py --wallet-file wallet.pem show-wallet
```

Create and submit a transaction:

```bash
python client.py --wallet-file wallet.pem send --recipient 0x1234 --amount 3 --fee 1
```

Retrieve and display the chain:

```bash
python client.py blocks
```

## Testing

### Run all tests

```bash
pytest
```

### Run only unit tests

```bash
pytest blockchain/tests/unit/
```

### Run security-focused tests

Security tests, marked with `@pytest.mark.security`, verify critical blockchain properties including:
- Transaction signature validation and tampering detection
- Prevention of double-spending and insufficient balance scenarios
- Chain integrity and tamper detection
- Wallet cryptographic operations and authentication

```bash
pytest blockchain/tests/ -m security
```

## Key Concepts

### Blocks

Blocks are immutable structures containing:
- Transaction list with merkle root
- Nonce (proof-of-work solution)
- Previous block hash (linking)
- Difficulty level
- Timestamp

### Transactions

Transactions are digitally signed transfers:
- Sender public key
- Recipient address
- Amount and fee
- ECDSA signature (SECP256K1 curve)

### Wallets

Wallets manage cryptographic keys:
- Private key for signing transactions
- Public key derivation (X962 format)
- Address calculation (SHA256 of public key)

### Mempool

Memory pool maintains pending transactions:
- Fee-based ordering (highest fee first)
- Stable sorting for equal fees
- O(1) lookup and removal by hash

### Mining

Mining (proof-of-work):
- Configurable difficulty
- Nonce search to find valid block hash
- Block reward + transaction fees
- Transaction selection from mempool

## Development

### Code Style

This project follows **PEP 8 guidelines** with:
- Maximum line length: 128 characters
- Type hints for all functions
- Comprehensive docstrings (PEP 257)
- Clear variable and function names

### Pre-commit Hooks

This project uses **pre-commit** to automatically enforce code quality checks before each commit:

- **Linting**: Ruff checks code style and catches common issues
- **Type Checking**: Pyright validates type hints and catches type errors
- **Formatting**: Code is automatically formatted to meet standards

Pre-commit hooks are configured in the Dev Container and run automatically when you commit. To manually run all checks without committing:

```bash
pre-commit run --all-files
```

The `.pre-commit-config.yaml` file defines all checks and their configuration. Pre-commit ensures code quality is maintained consistently across the codebase.

## References

- [Bitcoin Whitepaper](https://bitcoin.org/bitcoin.pdf)
- [Merkle Trees](https://en.wikipedia.org/wiki/Merkle_tree)
- [ECDSA - SECP256K1](https://en.wikipedia.org/wiki/Elliptic_Curve_Digital_Signature_Algorithm)
- [Proof of Work](https://en.wikipedia.org/wiki/Proof_of_work)

## License

See LICENSE file for details.

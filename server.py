"""Root-level launcher for the blockchain FastAPI server."""

import argparse

import uvicorn

from blockchain.app import create_app


if __name__ == "__main__":  # pragma: no cover
    """Start the blockchain API server."""
    parser = argparse.ArgumentParser(description="Start the blockchain FastAPI server.")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--log-level", default="info", help="Uvicorn log level")
    args = parser.parse_args()

    uvicorn.run(create_app(), host=args.host, port=args.port, log_level=args.log_level)

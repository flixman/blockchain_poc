import subprocess
import sys
import time

import pytest
import requests


@pytest.fixture
def server():
    proc = subprocess.Popen(
        [sys.executable, "server.py", "--port", "8001"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    base_url = "http://127.0.0.1:8001"
    for _ in range(10):
        try:
            requests.get(f"{base_url}/blocks", timeout=1)
            break
        except requests.RequestException:
            time.sleep(1)
    else:
        proc.terminate()
        raise RuntimeError("server did not start")

    yield base_url

    proc.terminate()
    proc.wait(timeout=10)


def run_client(*args):
    return subprocess.run(
        [sys.executable, "client.py", *args],
        capture_output=True,
        text=True,
    )


def test_client_can_fetch_blocks(server, tmp_path):
    wallet = tmp_path / "wallet.pem"

    result = run_client("--server", server, "--wallet-file", str(wallet), "init-wallet")
    assert result.returncode == 0

    result = run_client("--server", server, "--wallet-file", str(wallet), "blocks")
    assert result.returncode == 0
    assert "block index" in result.stderr or "block index" in result.stdout


def test_fresh_wallet_cannot_send(server, tmp_path):
    wallet = tmp_path / "wallet.pem"

    result = run_client("--server", server, "--wallet-file", str(wallet), "init-wallet")
    assert result.returncode == 0

    result = run_client(
        "--server",
        server,
        "--wallet-file",
        str(wallet),
        "send",
        "--recipient",
        "0x1234",
        "--amount",
        "1",
        "--fee",
        "0",
    )
    assert result.returncode != 0
    assert "Insufficient funds" in result.stderr or "insufficient" in result.stderr.lower()


def test_wallet_can_send(server, tmp_path):
    wallet = tmp_path / "wallet.pem"

    result = run_client("--server", server, "--wallet-file", str(wallet), "init-wallet")
    assert result.returncode == 0

    result = run_client("--server", server, "--wallet-file", str(wallet), "topup-wallet")
    assert result.returncode == 0

    result = run_client(
        "--server",
        server,
        "--wallet-file",
        str(wallet),
        "send",
        "--recipient",
        "0x1234",
        "--amount",
        "1",
        "--fee",
        "0",
    )
    assert result.returncode == 0
    assert "transaction accepted" in result.stderr

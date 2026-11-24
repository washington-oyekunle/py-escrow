"""Cryptographic primitives. HMAC-SHA256 by default (stdlib only).

Swap the implementation for real ECDSA/Ed25519 when you need production signatures.
"""

import hashlib
import hmac
import os
import secrets
from typing import Tuple


def generate_key() -> bytes:
    """Generate a 32-byte secret key."""
    return secrets.token_bytes(32)


def sign(key: bytes, message: bytes) -> bytes:
    """Produce an HMAC-SHA256 signature."""
    return hmac.new(key, message, hashlib.sha256).digest()


def verify(key: bytes, message: bytes, signature: bytes) -> bool:
    """Constant-time verification of an HMAC-SHA256 signature."""
    expected = sign(key, message)
    return hmac.compare_digest(expected, signature)


def hash_data(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def merkle_root(leaves: list[bytes]) -> bytes:
    """Simple binary Merkle root. Pads to next power of two."""
    if not leaves:
        return hash_data(b"")
    level = [hash_data(leaf) for leaf in leaves]
    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])
        level = [
            hash_data(level[i] + level[i + 1])
            for i in range(0, len(level), 2)
        ]
    return level[0]

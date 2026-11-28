"""Cryptographic primitives. HMAC-SHA256 by default (stdlib only).

Swap the implementation for real ECDSA/Ed25519 when you need production signatures.
"""

import hashlib
import hmac
import os
import secrets
from typing import List, Tuple


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


def merkle_root(leaves: List[bytes]) -> bytes:
    """Simple binary Merkle root. Pads to next power of two by duplicating last leaf."""
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


def generate_merkle_proof(leaves: List[bytes], index: int) -> List[Tuple[bytes, bool]]:
    """Generate an inclusion proof for the leaf at `index`.

    Returns a list of (sibling_hash, is_right) pairs from leaf to root.
    is_right=True means the sibling is on the right of the current node.
    """
    if not leaves or index < 0 or index >= len(leaves):
        raise IndexError("Invalid leaf index")

    level = [hash_data(leaf) for leaf in leaves]
    proof = []
    idx = index

    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])
        # Pair
        sibling_idx = idx ^ 1  # flip last bit
        is_right = (idx % 2 == 0)  # if even, sibling is on the right
        proof.append((level[sibling_idx], is_right))

        # Build next level
        next_level = []
        for i in range(0, len(level), 2):
            next_level.append(hash_data(level[i] + level[i + 1]))
        level = next_level
        idx //= 2

    return proof


def verify_merkle_proof(leaf: bytes, proof: List[Tuple[bytes, bool]], root: bytes) -> bool:
    """Verify an inclusion proof against a known root."""
    current = hash_data(leaf)
    for sibling, is_right in proof:
        if is_right:
            current = hash_data(current + sibling)
        else:
            current = hash_data(sibling + current)
    return hmac.compare_digest(current, root)

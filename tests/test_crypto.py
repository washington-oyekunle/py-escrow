"""Crypto primitive tests."""

from py_escrow.crypto import (
    generate_key,
    generate_merkle_proof,
    merkle_root,
    sign,
    verify,
    verify_merkle_proof,
)


def test_sign_verify():
    key = generate_key()
    msg = b"milestone-approved"
    sig = sign(key, msg)
    assert verify(key, msg, sig)
    assert not verify(key, b"tampered", sig)
    assert not verify(generate_key(), msg, sig)


def test_merkle():
    leaves = [b"event1", b"event2", b"event3"]
    root = merkle_root(leaves)
    assert len(root) == 32
    # Deterministic
    assert merkle_root(leaves) == root


def test_merkle_proof():
    leaves = [b"event1", b"event2", b"event3", b"event4"]
    root = merkle_root(leaves)

    for i in range(len(leaves)):
        proof = generate_merkle_proof(leaves, i)
        assert verify_merkle_proof(leaves[i], proof, root)

    # Tampered leaf should fail
    proof0 = generate_merkle_proof(leaves, 0)
    assert not verify_merkle_proof(b"tampered", proof0, root)

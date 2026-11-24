"""Crypto primitive tests."""

from py_escrow.crypto import generate_key, merkle_root, sign, verify


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

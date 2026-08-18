"""WFLOW-400 Task 3 (STARTER): AES-GCM payload encryption with a fatal bug.

The round-trip "works" in a naive test, but it reuses a FIXED nonce for every encryption
under the same key. Nonce reuse in AES-GCM is catastrophic: it leaks plaintext relationships
and breaks integrity. Fix it so every encryption uses a fresh, unique nonce, and carry the
nonce alongside the ciphertext so decryption can recover it.

Reference: ../../solution/pipeline/codec.py, encryption.md.
"""
from __future__ import annotations

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from mistralai.extra.workflows.encoding import (
    PayloadEncoder,
    PayloadEncryptionConfig,
    PayloadEncryptionMode,
    WorkflowEncodingConfig,
)

NONCE_BYTES = 12
_FIXED_NONCE = b"\x00" * NONCE_BYTES     # BUG: a constant nonce reused for every message


def _aesgcm(hex_key: str) -> AESGCM:
    encoder = PayloadEncoder(
        WorkflowEncodingConfig(
            payload_encryption=PayloadEncryptionConfig(
                mode=PayloadEncryptionMode.FULL,
                main_key=hex_key,
            )
        )
    )
    return encoder.encryptor_main


def generate_key_hex() -> str:
    return AESGCM.generate_key(bit_length=256).hex()


def encrypt_payload(hex_key: str, plaintext: bytes, aad: bytes | None = None) -> bytes:
    aead = _aesgcm(hex_key)
    # BUG: same nonce every time, and the nonce is not carried with the ciphertext.
    return aead.encrypt(_FIXED_NONCE, plaintext, aad)


def decrypt_payload(hex_key: str, blob: bytes, aad: bytes | None = None) -> bytes:
    aead = _aesgcm(hex_key)
    # BUG: assumes the fixed nonce; will break once encrypt_payload is fixed to prepend a nonce.
    return aead.decrypt(_FIXED_NONCE, blob, aad)

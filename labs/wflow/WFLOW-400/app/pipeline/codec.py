"""WFLOW-400 Task 3 (SOLUTION): AES-GCM payload encryption, done correctly.

Workflows encrypts payloads on the worker before they leave (see encryption.md). Under the
hood the SDK's encoder exposes a `cryptography` AES-GCM cipher built from a 256-bit hex key
(PayloadEncoder.encryptor_main). We use that exact primitive here.

The load-bearing rule of AES-GCM: **the nonce MUST be unique for every encryption under a
given key.** Reusing a nonce destroys both confidentiality and integrity. We therefore
generate a fresh 12-byte nonce per call and prepend it to the ciphertext so the reader can
recover it. This runs live crypto; nothing is mocked.
"""
from __future__ import annotations

import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from mistralai.extra.workflows.encoding import (
    PayloadEncoder,
    PayloadEncryptionConfig,
    PayloadEncryptionMode,
    WorkflowEncodingConfig,
)

NONCE_BYTES = 12


def _aesgcm(hex_key: str) -> AESGCM:
    """Build the SAME AES-GCM cipher the Workflows SDK uses, from a 256-bit hex key."""
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
    """Generate a 256-bit AES-GCM key as hex (store this in a secret manager)."""
    return AESGCM.generate_key(bit_length=256).hex()


def encrypt_payload(hex_key: str, plaintext: bytes, aad: bytes | None = None) -> bytes:
    aead = _aesgcm(hex_key)
    nonce = os.urandom(NONCE_BYTES)          # fresh, unique nonce for every encryption
    ciphertext = aead.encrypt(nonce, plaintext, aad)
    return nonce + ciphertext                # prepend the nonce for the reader


def decrypt_payload(hex_key: str, blob: bytes, aad: bytes | None = None) -> bytes:
    aead = _aesgcm(hex_key)
    nonce, ciphertext = blob[:NONCE_BYTES], blob[NONCE_BYTES:]
    return aead.decrypt(nonce, ciphertext, aad)

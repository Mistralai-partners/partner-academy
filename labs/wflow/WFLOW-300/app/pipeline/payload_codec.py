"""WFLOW-300 Task 10 (SOLUTION): offload a large field AND encrypt a sensitive one.

A document-processing payload has two fields that must not travel naively on the orchestration
layer:

  - A large body (an extracted transcript / OCR text) that can blow past the 2MB workflow I/O
    cap. You mark it an `OffloadableField` on an `OffloadableModel`: the SDK stores it in your
    blob storage on the way out of an activity and rehydrates it on the way in, so the
    orchestrator only ever carries a small reference. Call `.get_value()` ONLY inside
    activities; pass the field through untouched in the workflow body.

  - A sensitive field (an SSN, an API secret) that must be unreadable if intercepted. You
    encrypt it with AES-GCM using the SAME cipher the SDK's PayloadEncoder builds from a
    256-bit hex key. The load-bearing rule: the nonce MUST be unique per encryption under a
    given key, so we draw a fresh 12-byte nonce each call and prepend it to the ciphertext.

Grounded in: building-workflows/payload_offloading.md (Activity field offloading),
building-workflows/encryption.md (payloads encrypted on the worker; AES-GCM via PayloadEncoder).
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
from mistralai.workflows.core.encoding.fields_offloader import (
    OffloadableField,
    OffloadableModel,
)

import mistralai.workflows as workflows

NONCE_BYTES = 12


# ---- AES-GCM for the sensitive field -------------------------------------------------
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


# ---- Offloadable model for the large field -------------------------------------------
class DocumentPayload(OffloadableModel):
    doc_id: str                                            # small reference — stays on the layer
    sensitive_hex: str = ""                                # AES-GCM ciphertext, hex-encoded
    body: OffloadableField[str] = OffloadableField(value="")  # large (>2MB) — offloaded


@workflows.activity()
async def extract_document(doc_id: str, sensitive: str, hex_key: str) -> DocumentPayload:
    # Inside an activity: producing the large body and reading/encrypting the sensitive field
    # are both fine here. get_value() is only unsafe in the workflow body.
    body_text = f"extracted-{doc_id}: " + ("lorem " * 16).strip()
    sealed = encrypt_payload(hex_key, sensitive.encode()).hex()
    return DocumentPayload(
        doc_id=doc_id,
        sensitive_hex=sealed,
        body=OffloadableField(value=body_text),
    )


@workflows.activity()
async def summarize_document(payload: DocumentPayload, hex_key: str) -> dict:
    # The offloaded body is rehydrated for us here; get_value() is safe INSIDE an activity.
    full = payload.body.get_value()
    ssn = decrypt_payload(hex_key, bytes.fromhex(payload.sensitive_hex)).decode()
    return {"summary": full[:20], "chars": len(full), "ssn_last4": ssn[-4:]}


@workflows.workflow.define(name="document-workflow")
class DocumentWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, doc_id: str, sensitive: str, hex_key: str) -> dict:
        payload = await extract_document(doc_id, sensitive, hex_key)
        # Pass the offloaded field through as-is — do NOT unwrap it in the workflow body.
        return await summarize_document(payload, hex_key)

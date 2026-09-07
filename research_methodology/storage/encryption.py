"""At-rest encryption seam (§9.9/§6b).

Layer 1 provides the passthrough IdentityEncryptor. A real Fernet/SQLCipher
Encryptor is a deferred later task; because callers depend only on this
protocol, swapping it in never touches store code.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Encryptor(Protocol):
    def encrypt(self, plaintext: bytes) -> bytes: ...
    def decrypt(self, ciphertext: bytes) -> bytes: ...


class IdentityEncryptor:
    """Dev/test passthrough. NOT for production data at rest."""

    def encrypt(self, plaintext: bytes) -> bytes:
        return plaintext

    def decrypt(self, ciphertext: bytes) -> bytes:
        return ciphertext

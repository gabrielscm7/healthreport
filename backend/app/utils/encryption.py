import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _get_key() -> bytes:
    key = os.getenv("ENCRYPTION_KEY", "")
    if not key:
        key = os.getenv("SECRET_KEY", "fallback-key-32-chars!!")
    key_bytes = key.encode("utf-8")
    if len(key_bytes) < 32:
        key_bytes = key_bytes.ljust(32, b"\x00")
    return key_bytes[:32]


def encrypt_aes256(plaintext: str) -> tuple[bytes, bytes, bytes]:
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    tag = ciphertext[-16:]
    ciphertext_without_tag = ciphertext[:-16]
    return ciphertext_without_tag, nonce, tag


def decrypt_aes256(ciphertext: bytes, nonce: bytes, tag: bytes) -> str:
    key = _get_key()
    aesgcm = AESGCM(key)
    full_ciphertext = ciphertext + tag
    plaintext = aesgcm.decrypt(nonce, full_ciphertext, None)
    return plaintext.decode("utf-8")

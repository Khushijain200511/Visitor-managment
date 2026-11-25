import base64
import hashlib
from cryptography.fernet import Fernet


def fernet_from_client_name(client_name: str) -> Fernet:

    digest = hashlib.sha256(client_name.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_str(f: Fernet, s: str | None) -> str | None:
    if s is None:
        return None
    return f.encrypt(s.encode("utf-8")).decode("utf-8")


def decrypt_str(f: Fernet, s: str | None) -> str | None:
    if s is None:
        return None
    try:
        return f.decrypt(s.encode("utf-8")).decode("utf-8")
    except Exception:
        return s 
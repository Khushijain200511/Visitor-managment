from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
Path("private_key.pem").write_bytes(key.private_bytes(
    serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption()))
Path("public_key.pem").write_bytes(key.public_key().public_bytes(
    serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
print("Done. Ship public_key.pem; keep private_key.pem offline.")
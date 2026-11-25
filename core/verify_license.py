import base64
import json
from datetime import date
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key

from core.machine_id import get_machine_id

LICENSE_DIR = Path(r"C:\ProgramData\VisitorManagement")
LICENSE_FILE = LICENSE_DIR / "license.lic"
PUBLIC_KEY_PATH = Path(__file__).resolve().parent.parent / "public_key.pem"


def load_license(path: Path = LICENSE_FILE) -> dict | None:
    if not path.exists():
        print(f"DEBUG: License file NOT found at {path}")
        return None
        
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        payload_b64 = data["payload"]
        signature = base64.b64decode(data["signature"])
        payload_bytes = base64.b64decode(payload_b64)
        
        if not PUBLIC_KEY_PATH.exists():
            print(f"DEBUG: Public key NOT found at {PUBLIC_KEY_PATH}")
            return None
            
        pub = load_pem_public_key(PUBLIC_KEY_PATH.read_bytes())
        
        try:
            pub.verify(
                signature, payload_bytes,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
                hashes.SHA256(),
            )
        except InvalidSignature:
            print("DEBUG: Invalid Signature! License file might be corrupted or generated with a different private key.")
            return None
            
        payload = json.loads(payload_bytes)
        
    except Exception as e:
        print(f"DEBUG: Error reading or parsing license: {e}")
        return None

    if date.fromisoformat(payload["expiry_date"]) < date.today():
        print(f"DEBUG: License expired on {payload['expiry_date']}")
        return None
        
    actual_machine_id = get_machine_id()
    if payload["machine_id"] != actual_machine_id:
        print(f"DEBUG: Machine ID mismatch!")
        print(f"  -> License ID: {payload['machine_id']}")
        print(f"  -> Your PC ID: {actual_machine_id}")
        return None
        
    print("DEBUG: License verified successfully!")
    return payload
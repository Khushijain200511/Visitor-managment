import sys
from core.crypto_utils import fernet_from_client_name, encrypt_str, decrypt_str
from core.database import Database, PERSONAL_VISITOR, PERSONAL_PARCEL

path, old_client, new_client = sys.argv[1:4]
old = fernet_from_client_name(old_client)
new = fernet_from_client_name(new_client)
db = Database(path, new_client)
with db.lock, db.conn:
    for table, fields in (("visitors", PERSONAL_VISITOR), ("parcels", PERSONAL_PARCEL)):
        for row in db.conn.execute(f"SELECT * FROM {table}").fetchall():
            for k in fields:
                if row[k]:
                    db.conn.execute(f"UPDATE {table} SET {k}=? WHERE id=?",
                                    (encrypt_str(new, decrypt_str(old, row[k])), row["id"]))
print("Rekey complete.")
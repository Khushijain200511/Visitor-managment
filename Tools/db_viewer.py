import sys, json
from pathlib import Path
from core.database import Database

db = Database(sys.argv[1], sys.argv[2])  # path client_name
for table in ("visitors", "parcels"):
    print(f"\n=== {table} ===")
    for r in db.all_rows(table):
        print(json.dumps(r, indent=2, default=str))
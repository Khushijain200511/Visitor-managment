import sqlite3
import threading
from datetime import datetime, date
from pathlib import Path

from core.crypto_utils import fernet_from_client_name, encrypt_str, decrypt_str

PERSONAL_VISITOR = ["name", "mobile", "email", "address", "whom_to_meet",
                    "purpose", "id_number", "things_deposited"]
PERSONAL_PARCEL = ["sender_name", "sender_phone", "recipient_name",
                   "recipient_phone", "delivery_person_name",
                   "delivery_person_phone", "parcel_description", "notes"]


class Database:
    def __init__(self, db_path: str | Path, client_name: str):
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        self.f = fernet_from_client_name(client_name)
        self._create_tables()

  
    def _create_tables(self):
        with self.lock, self.conn:
            self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS visitors(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, mobile TEXT, email TEXT, address TEXT,
                whom_to_meet TEXT, purpose TEXT, id_type TEXT, id_number TEXT,
                locker_assigned TEXT, things_deposited TEXT,
                check_in_time TEXT, check_out_time TEXT,
                check_in_date TEXT, check_in_time_only TEXT,
                check_out_time_only TEXT,
                status TEXT DEFAULT 'Checked-in',
                photo_path TEXT, checkout_photo_path TEXT,
                officer_permission TEXT, visitor_number TEXT UNIQUE
            );
            CREATE TABLE IF NOT EXISTS parcels(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_name TEXT, sender_phone TEXT,
                recipient_name TEXT, recipient_phone TEXT,
                delivery_person_name TEXT, delivery_person_phone TEXT,
                parcel_description TEXT, notes TEXT,
                deposit_time TEXT, deposit_date TEXT, deposit_time_only TEXT,
                deposit_receptionist TEXT,
                pickup_time TEXT, pickup_date TEXT, pickup_time_only TEXT,
                pickup_receptionist TEXT,
                status TEXT DEFAULT 'Deposited'
            );
            CREATE TABLE IF NOT EXISTS features_config(
                feature_key TEXT PRIMARY KEY, feature_name TEXT,
                enabled INTEGER DEFAULT 0, description TEXT,
                created_at TEXT, updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS app_meta(key TEXT PRIMARY KEY, value TEXT);
            """)

    
    def _enc(self, row: dict, fields) -> dict:
        return {k: (encrypt_str(self.f, v) if k in fields and v is not None else v)
                for k, v in row.items()}

    def _dec(self, row: sqlite3.Row, fields) -> dict:
        d = dict(row)
        for k in fields:
            if k in d:
                d[k] = decrypt_str(self.f, d[k])
        return d

    def _next_visitor_number(self, d: str) -> str:
        cur = self.conn.execute(
            "SELECT COUNT(*) FROM visitors WHERE check_in_date=?", (d,))
        n = (cur.fetchone()[0] or 0) + 1
        yyyy, mm, dd = d.split("-")
        return f"{yyyy}/{mm}/{dd}/{n}"

    
    def add_visitor(self, data: dict) -> dict:
        now = datetime.now()
        d = now.strftime("%Y-%m-%d")
        with self.lock, self.conn:
            vnum = self._next_visitor_number(d)
            row = {
                **data,
                "check_in_time": now.strftime("%Y-%m-%d %H:%M:%S"),
                "check_in_date": d,
                "check_in_time_only": now.strftime("%H:%M:%S"),
                "status": "Checked-in",
                "visitor_number": vnum,
            }
            row = self._enc(row, PERSONAL_VISITOR)
            cols = ",".join(row)
            qs = ",".join("?" * len(row))
            self.conn.execute(f"INSERT INTO visitors({cols}) VALUES({qs})",
                              list(row.values()))
            rid = self.conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return self.get_visitor(rid)

    def get_visitor(self, vid: int) -> dict | None:
        with self.lock:
            r = self.conn.execute("SELECT * FROM visitors WHERE id=?", (vid,)).fetchone()
        return self._dec(r, PERSONAL_VISITOR) if r else None

    def find_last_visit_by_mobile(self, mobile: str) -> dict | None:
        """Encrypted column: decrypt & match in Python."""
        with self.lock:
            rows = self.conn.execute(
                "SELECT * FROM visitors ORDER BY id DESC LIMIT 500").fetchall()
        for r in rows:
            d = self._dec(r, PERSONAL_VISITOR)
            if d.get("mobile") == mobile:
                return d
        return None

    def today_visitors(self) -> list[dict]:
        d = date.today().isoformat()
        with self.lock:
            rows = self.conn.execute(
                "SELECT * FROM visitors WHERE check_in_date=? ORDER BY id DESC", (d,)
            ).fetchall()
        return [self._dec(r, PERSONAL_VISITOR) for r in rows]

    def dashboard_counts(self) -> dict:
        d = date.today().isoformat()
        with self.lock:
            total = self.conn.execute(
                "SELECT COUNT(*) FROM visitors WHERE check_in_date=?", (d,)).fetchone()[0]
            out = self.conn.execute(
                "SELECT COUNT(*) FROM visitors WHERE check_in_date=? AND status='Checked-out'",
                (d,)).fetchone()[0]
            inside = self.conn.execute(
                "SELECT COUNT(*) FROM visitors WHERE status='Checked-in'").fetchone()[0]
        return {"today": total, "out": out, "inside": inside}

    def checked_in(self) -> list[dict]:
        with self.lock:
            rows = self.conn.execute(
                "SELECT * FROM visitors WHERE status='Checked-in' ORDER BY id DESC").fetchall()
        return [self._dec(r, PERSONAL_VISITOR) for r in rows]

    def checkout_visitor(self, vid: int, checkout_photo_path: str) -> None:
        now = datetime.now()
        with self.lock, self.conn:
            self.conn.execute(
                """UPDATE visitors SET check_out_time=?, check_out_time_only=?,
                   checkout_photo_path=?, status='Checked-out' WHERE id=?""",
                (now.strftime("%Y-%m-%d %H:%M:%S"), now.strftime("%H:%M:%S"),
                 checkout_photo_path, vid))

    def search_visitors(self, on_date: str | None = None,
                        status: str | None = None,
                        text: str = "") -> list[dict]:
        sql, args = "SELECT * FROM visitors WHERE 1=1", []
        if on_date:
            sql += " AND check_in_date=?"; args.append(on_date)
        if status and status != "All":
            sql += " AND status=?"; args.append(status)
        sql += " ORDER BY id DESC"
        with self.lock:
            rows = self.conn.execute(sql, args).fetchall()
        out = [self._dec(r, PERSONAL_VISITOR) for r in rows]
        if text:
            t = text.lower()
            out = [r for r in out if any(t in (r.get(k) or "").lower()
                   for k in ("name", "mobile", "visitor_number", "whom_to_meet"))]
        return out

   
    def add_parcel(self, data: dict) -> None:
        now = datetime.now()
        row = {
            **data,
            "deposit_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "deposit_date": now.strftime("%Y-%m-%d"),
            "deposit_time_only": now.strftime("%H:%M:%S"),
            "status": "Deposited",
        }
        row = self._enc(row, PERSONAL_PARCEL)
        with self.lock, self.conn:
            cols = ",".join(row); qs = ",".join("?" * len(row))
            self.conn.execute(f"INSERT INTO parcels({cols}) VALUES({qs})", list(row.values()))

    def parcels(self, status: str | None = None, text: str = "") -> list[dict]:
        sql, args = "SELECT * FROM parcels WHERE 1=1", []
        if status and status != "All":
            sql += " AND status=?"; args.append(status)
        with self.lock:
            rows = self.conn.execute(sql + " ORDER BY id DESC", args).fetchall()
        out = [self._dec(r, PERSONAL_PARCEL) for r in rows]
        if text:
            t = text.lower()
            out = [r for r in out if any(t in (r.get(k) or "").lower()
                   for k in ("sender_name", "recipient_name", "parcel_description"))]
        return out

    def pickup_parcel(self, pid: int, receptionist: str) -> None:
        now = datetime.now()
        with self.lock, self.conn:
            self.conn.execute(
                """UPDATE parcels SET pickup_time=?, pickup_date=?, pickup_time_only=?,
                   pickup_receptionist=?, status='Picked Up' WHERE id=?""",
                (now.strftime("%Y-%m-%d %H:%M:%S"), now.strftime("%Y-%m-%d"),
                 now.strftime("%H:%M:%S"), receptionist, pid))

   
    def set_feature(self, key, name, enabled, description=""):
        now = datetime.now().isoformat(timespec="seconds")
        with self.lock, self.conn:
            self.conn.execute(
                """INSERT INTO features_config(feature_key,feature_name,enabled,
                   description,created_at,updated_at) VALUES(?,?,?,?,?,?)
                   ON CONFLICT(feature_key) DO UPDATE SET enabled=excluded.enabled,
                   updated_at=excluded.updated_at""",
                (key, name, int(enabled), description, now, now))

    def get_features(self) -> list[dict]:
        with self.lock:
            rows = self.conn.execute("SELECT * FROM features_config").fetchall()
        return [dict(r) for r in rows]

    def feature_enabled(self, key) -> bool:
        with self.lock:
            r = self.conn.execute(
                "SELECT enabled FROM features_config WHERE feature_key=?", (key,)).fetchone()
        return bool(r and r[0])

    def all_rows(self, table: str) -> list[dict]:
        with self.lock:
            rows = self.conn.execute(f"SELECT * FROM {table}").fetchall()
        fields = PERSONAL_VISITOR if table == "visitors" else PERSONAL_PARCEL
        return [self._dec(r, fields) for r in rows]
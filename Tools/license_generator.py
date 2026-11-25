import base64, json
from datetime import date, timedelta
from pathlib import Path
from tkinter import Tk, Entry, Label, Button, messagebox, filedialog
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key

PRIV = load_pem_private_key(Path("private_key.pem").read_bytes(), password=None)
FEATURES = ["parcels", "backup"]

def make_license(client, machine_id, expiry, features):
    payload = {"client_name": client, "machine_id": machine_id,
               "expiry_date": expiry, "features": features}
    raw = json.dumps(payload, separators=(",", ":")).encode()
    sig = PRIV.sign(raw, padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                                     salt_length=32), hashes.SHA256())
    return {"payload": base64.b64encode(raw).decode(),
            "signature": base64.b64encode(sig).decode()}

def ui():
    r = Tk(); r.title("License generator"); r.geometry("460x300")
    entries = {}
    for i, (k, default) in enumerate([
        ("client_name", "DGGI Mumbai"),
        ("machine_id", ""),
        ("expiry_date", (date.today() + timedelta(days=365)).isoformat()),
    ]):
        Label(r, text=k).grid(row=i, column=0, sticky="e")
        e = Entry(r, width=40); e.insert(0, default); e.grid(row=i, column=1)
        entries[k] = e
    feat_vars = {}
    for i, f in enumerate(FEATURES):
        from tkinter import IntVar, Checkbutton
        v = IntVar(value=1); feat_vars[f] = v
        Checkbutton(r, text=f, variable=v).grid(row=3+i, column=1, sticky="w")
    def save():
        feats = [k for k, v in feat_vars.items() if v.get()]
        lic = make_license(entries["client_name"].get(), entries["machine_id"].get(),
                           entries["expiry_date"].get(), feats)
        p = filedialog.asksaveasfilename(defaultextension=".lic")
        if p:
            Path(p).write_text(json.dumps(lic, indent=2))
            messagebox.showinfo("Saved", p)
    Button(r, text="Generate .lic", command=save).grid(row=8, column=1, pady=10)
    r.mainloop()

if __name__ == "__main__": ui()
import customtkinter as ctk
from tkinter import ttk, messagebox

class ParcelManagement(ctk.CTkFrame):
    def __init__(self, master, db, app):
        super().__init__(master, fg_color="transparent")
        self.db, self.app = db, app
        form = ctk.CTkFrame(self); form.pack(fill="x", padx=8, pady=8)
        keys = ["sender_name","sender_phone","recipient_name","recipient_phone",
                "delivery_person_name","delivery_person_phone",
                "parcel_description","notes"]
        self.entries = {}
        for i,k in enumerate(keys):
            e = ctk.CTkEntry(form, placeholder_text=k.replace("_"," ").title(), width=180)
            e.grid(row=i//4, column=i%4, padx=4, pady=4); self.entries[k]=e
        ctk.CTkEntry(form, textvariable=ctk.StringVar(value="reception"),
                     state="normal")  # receptionist stub
        ctk.CTkButton(form, text="Log Deposit", command=self._deposit).grid(row=2, column=0, pady=6)
        ctk.CTkButton(form, text="Mark Picked Up", command=self._pickup).grid(row=2, column=1, pady=6)

        self.tree = ttk.Treeview(self, columns=("id","sender","recipient","status","deposit","pickup"),
                                 show="headings")
        for c,h in zip(self.tree["columns"],
                       ("ID","Sender","Recipient","Status","Deposited","Picked up")):
            self.tree.heading(c, text=h); self.tree.column(c, width=160)
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)
        self._load()

    def _deposit(self):
        self.db.add_parcel({k:e.get() for k,e in self.entries.items()})
        self._load()

    def _pickup(self):
        sel = self.tree.selection()
        if not sel: return
        pid = int(self.tree.item(sel[0])["values"][0])
        self.db.pickup_parcel(pid, "reception")
        self._load()

    def _load(self):
        self.tree.delete(*self.tree.get_children())
        for p in self.db.parcels():
            self.tree.insert("", "end", values=(
                p["id"], p["sender_name"], p["recipient_name"], p["status"],
                p["deposit_time"], p.get("pickup_time") or ""))
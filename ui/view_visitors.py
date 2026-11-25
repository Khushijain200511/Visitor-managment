import csv
from pathlib import Path
from tkinter import ttk, filedialog
import customtkinter as ctk
from tkcalendar import DateEntry
from ui.widgets import Tooltip

class ViewVisitors(ctk.CTkFrame):
    def __init__(self, master, db, app):
        super().__init__(master, fg_color="transparent")
        self.db, self.app = db, app
        bar = ctk.CTkFrame(self); bar.pack(fill="x", pady=6)
        self.date = DateEntry(bar, date_pattern="yyyy-mm-dd"); self.date.pack(side="left", padx=6)
        self.status = ctk.CTkOptionMenu(bar, values=["All","Checked-in","Checked-out"]); self.status.pack(side="left", padx=6)
        self.search = ctk.CTkEntry(bar, placeholder_text="Search name / mobile / number", width=280)
        self.search.pack(side="left", padx=6)
        ctk.CTkButton(bar, text="Apply", command=self.load).pack(side="left", padx=6)
        ctk.CTkButton(bar, text="Export CSV", command=self.export).pack(side="left", padx=6)

        cols = ("num","name","mobile","email","meet","purpose","in","out","status")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        heads = ("#","Name","Mobile","Email","Meeting","Purpose","In","Out","Status")
        for c,h in zip(cols, heads):
            self.tree.heading(c, text=h); self.tree.column(c, width=120)
        self.tree.pack(fill="both", expand=True)
        Tooltip(self.tree, self._current_full)
        self.rows = []
        self.load()

    def load(self):
        self.rows = self.db.search_visitors(
            on_date=self.date.get(), status=self.status.get(),
            text=self.search.get().strip())
        self.tree.delete(*self.tree.get_children())
        for r in self.rows:
            vals = [r["visitor_number"], r["name"], r["mobile"], r["email"],
                    r["whom_to_meet"], r["purpose"], r["check_in_time_only"],
                    r["check_out_time_only"] or "", r["status"]]
            vals = [(v[:28] + "…") if v and len(str(v)) > 30 else v for v in vals]
            self.tree.insert("", "end", values=vals)

    def _current_full(self):
        sel = self.tree.selection()
        if not sel: return ""
        i = self.tree.index(sel[0])
        r = self.rows[i]
        return "\n".join(f"{k}: {r.get(k,'')}" for k in
                         ("visitor_number","name","mobile","email","address",
                          "whom_to_meet","purpose","id_type","id_number"))

    def export(self):
        p = filedialog.asksaveasfilename(defaultextension=".csv")
        if not p: return
        with open(p, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=self.rows[0].keys() if self.rows else ["info"])
            if self.rows: w.writeheader(); w.writerows(self.rows)
        print("Saved", p)
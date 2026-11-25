import customtkinter as ctk
from tkinter import ttk

class Dashboard(ctk.CTkFrame):
    def __init__(self, master, db, app):
        super().__init__(master, fg_color="transparent")
        self.db, self.app = db, app
        cards = ctk.CTkFrame(self, fg_color="transparent"); cards.pack(fill="x", pady=10)
        self.labels = {}
        for i, (k, title) in enumerate([("today","Today's visitors"),
                                        ("out","Checked-out"),
                                        ("inside","Currently inside")]):
            c = ctk.CTkFrame(cards); c.grid(row=0, column=i, padx=8, sticky="ew")
            ctk.CTkLabel(c, text=title, font=("", 13)).pack(padx=25, pady=(12,0))
            v = ctk.CTkLabel(c, text="0", font=("", 26, "bold")); v.pack(padx=25, pady=(0,12))
            self.labels[k] = v
        cols = ("num","name","mobile","meet","in","status")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=18)
        for c,t in zip(cols, ("#","Name","Mobile","Meeting","In","Status")):
            self.tree.heading(c, text=t); self.tree.column(c, width=130)
        self.tree.pack(fill="both", expand=True)
        self.refresh()

    def refresh(self):
        c = self.db.dashboard_counts()
        for k in self.labels: self.labels[k].configure(text=str(c[k]))
        self.tree.delete(*self.tree.get_children())
        for v in self.db.today_visitors():
            self.tree.insert("", "end", values=(v["visitor_number"], v["name"],
                v["mobile"], v["whom_to_meet"], v["check_in_time_only"], v["status"]))
        self.after(3000, self.refresh)
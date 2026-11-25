import customtkinter as ctk
from core.feature_management import FEATURES

class FeatureSelectionDialog(ctk.CTkToplevel):
    def __init__(self, master, allowed: list[str], on_done):
        super().__init__(master)
        self.on_done = on_done; self.vars = {}
        self.title("Choose features"); self.geometry("360x260"); self.grab_set()
        ctk.CTkLabel(self, text="Enable optional features",
                     font=("", 16, "bold")).pack(pady=10)
        for key in allowed:
            name, desc = FEATURES[key]
            v = ctk.BooleanVar(value=True)
            ctk.CTkCheckBox(self, text=f"{name} — {desc}", variable=v).pack(anchor="w", padx=20, pady=4)
            self.vars[key] = v
        ctk.CTkButton(self, text="Continue", command=self._done).pack(pady=10)

    def _done(self):
        self.on_done([k for k,v in self.vars.items() if v.get()])
        self.destroy()
import re
import tkinter as tk

NAME_RE = re.compile(r"^[A-Za-z ]+$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ID_RULES = {
    "Aadhaar": re.compile(r"^\d{12}$"),
    "PAN": re.compile(r"^[A-Z]{5}\d{4}[A-Z]$"),
    "Passport": re.compile(r"^[A-Z0-9]{6,12}$"),
    "Driving License": re.compile(r"^[A-Z0-9]{6,20}$"),
    "Voter ID": re.compile(r"^[A-Z0-9]{8,12}$"),
    "Other": re.compile(r"^.+$"),
}

def validate_visitor(form: dict) -> dict[str, str]:
    e = {}
    if not NAME_RE.match(form.get("name", "")): e["name"] = "Letters and spaces only"
    m = form.get("mobile", "")
    if not (m.isdigit() and len(m) == 10 and set(m) != {"0"}):
        e["mobile"] = "Exactly 10 digits, not all zeros"
    em = form.get("email", "")
    if em != "N/A" and not EMAIL_RE.match(em): e["email"] = "Valid email or N/A"
    it, num = form.get("id_type", "Other"), form.get("id_number", "")
    if not ID_RULES.get(it, ID_RULES["Other"]).match(num):
        e["id_number"] = f"Invalid {it} number"
    if not form.get("photo_path"): e["photo"] = "Photo required"
    return e

class Tooltip:
    def __init__(self, widget, text_getter):
        self.w, self.get = widget, text_getter
        self.tip = None
        widget.bind("<Enter>", self._show); widget.bind("<Leave>", self._hide)
    def _show(self, _):
        text = self.get()
        if not text: return
        x = self.w.winfo_rootx() + 20; y = self.w.winfo_rooty() + 20
        self.tip = tk.Toplevel(self.w); self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tip, text=text, bg="#ffffe0", relief="solid",
                 borderwidth=1, wraplength=350, justify="left").pack()
    def _hide(self, _):
        if self.tip: self.tip.destroy(); self.tip = None
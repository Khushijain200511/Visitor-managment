from pathlib import Path
import time, cv2, customtkinter as ctk
from PIL import Image
from tkinter import messagebox
from core.template_pass import generate_receipt

DATA = Path("data")

class CheckoutVisitor(ctk.CTkFrame):
    def __init__(self, master, db, app):
        super().__init__(master, fg_color="transparent")
        self.db, self.app, self.selected = db, app, None
        left = ctk.CTkFrame(self); left.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(left, text="Search checked-in visitors").pack(anchor="w")
        self.q = ctk.CTkEntry(left, width=360); self.q.pack(anchor="w", pady=4)
        self.q.bind("<KeyRelease>", lambda e: self._search())
        self.listbox = ctk.CTkScrollableFrame(left, width=380, height=460)
        self.listbox.pack(fill="both", expand=True, pady=6)
        self._search()

        right = ctk.CTkFrame(self); right.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        self.info = ctk.CTkLabel(right, text="Select a visitor"); self.info.pack()
        self.photo_label = ctk.CTkLabel(right, text="Check-in photo"); self.photo_label.pack(pady=6)
        self.cam = ctk.CTkLabel(right, text="Checkout camera", width=320, height=240); self.cam.pack(pady=6)
        ctk.CTkButton(right, text="Capture & Checkout", command=self._checkout).pack(pady=6)
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self._loop()

    def _search(self):
        for w in self.listbox.winfo_children(): w.destroy()
        rows = self.db.checked_in()
        t = self.q.get().lower()
        for r in rows:
            if t and t not in (r["name"] or "").lower() and t not in (r["mobile"] or ""):
                continue
            ctk.CTkButton(self.listbox, text=f"{r['visitor_number']} {r['name']}",
                          command=lambda rr=r: self._select(rr)).pack(fill="x", pady=2)

    def _select(self, r):
        self.selected = r
        self.info.configure(text=f"{r['name']} | {r['mobile']} | In: {r['check_in_time']}")
        p = r.get("photo_path")
        if p and Path(p).exists():
            img = ctk.CTkImage(Image.open(p), size=(200,250))
            self.photo_label.configure(image=img, text="")

    def _loop(self):
        if self.cap and self.cap.isOpened():
            ok, frm = self.cap.read()
            if ok:
                self.last = frm
                rgb = cv2.cvtColor(frm, cv2.COLOR_BGR2RGB)
                self.cam.configure(image=ctk.CTkImage(Image.fromarray(rgb), size=(320,240)), text="")
        self.after(30, self._loop)

    def _checkout(self):
        if not self.selected: return
        DATA.joinpath("photos").mkdir(parents=True, exist_ok=True)
        p = DATA / "photos" / f"{self.selected['visitor_number'].replace('/','-')}_out.jpg"
        cv2.imwrite(str(p), self.last)
        self.db.checkout_visitor(self.selected["id"], str(p))
        v = self.db.get_visitor(self.selected["id"])
        rp = DATA / "passes" / f"{v['visitor_number'].replace('/','-')}_receipt.pdf"
        generate_receipt(v, rp)
        messagebox.showinfo("Checked out", f"Receipt: {rp}")
        self._search()
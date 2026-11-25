import time
from pathlib import Path
import cv2
import customtkinter as ctk
from PIL import Image
from tkinter import messagebox
from core.template_pass import generate_pass
from ui.widgets import validate_visitor

DATA = Path("data")

class AddVisitor(ctk.CTkFrame):
    def __init__(self, master, db, app):
        super().__init__(master, fg_color="transparent")
        self.db, self.app = db, app
        self.cap = None
        self.photo_path = None
        self.errors = {}
        self.entries = {}
        form = ctk.CTkScrollableFrame(self, width=480); form.pack(side="left", fill="both", padx=10, pady=10)
        fields = [("name","Name"),("mobile","Mobile"),("email","Email (or N/A)"),
                  ("address","Address"),("whom_to_meet","Whom to meet"),
                  ("purpose","Purpose"),("locker_assigned","Locker #"),
                  ("things_deposited","Items deposited"),("id_number","ID number")]
        for i,(k,label) in enumerate(fields):
            ctk.CTkLabel(form, text=label, anchor="w").grid(row=i*2, column=0, sticky="w", pady=(6,0))
            e = ctk.CTkEntry(form, width=420); e.grid(row=i*2+1, column=0, sticky="w")
            e.bind("<KeyRelease>", self._live_validate)
            self.entries[k] = e
            err = ctk.CTkLabel(form, text="", text_color="red", anchor="w")
            err.grid(row=i*2+1, column=1, sticky="w"); self.errors[k] = err
        self.entries["mobile"].bind("<KeyRelease>", self._autofill_mobile)

        r = len(fields)*2
        ctk.CTkLabel(form, text="ID type").grid(row=r, column=0, sticky="w", pady=(6,0))
        self.id_type = ctk.CTkOptionMenu(form, values=list(
            ["Aadhaar","PAN","Passport","Driving License","Voter ID","Other"]))
        self.id_type.grid(row=r+1, column=0, sticky="w")
        ctk.CTkLabel(form, text="Officer permission?").grid(row=r+2, column=0, sticky="w", pady=(6,0))
        self.perm = ctk.CTkOptionMenu(form, values=["Yes","No"]); self.perm.grid(row=r+3, column=0, sticky="w")
        self.cam_choice = ctk.CTkOptionMenu(form, values=["Camera 0","Camera 1","Camera 2"])
        self.cam_choice.grid(row=r+4, column=0, sticky="w", pady=(6,0))
        ctk.CTkButton(form, text="Capture Photo", command=self.capture).grid(row=r+5, column=0, pady=8, sticky="w")
        ctk.CTkButton(form, text="Submit", command=self.submit).grid(row=r+6, column=0, pady=10, sticky="w")

        right = ctk.CTkFrame(self); right.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        self.preview = ctk.CTkLabel(right, text="Camera preview", width=480, height=360)
        self.preview.pack(pady=10)
        self.start_camera()

    def start_camera(self):
        idx = int(self.cam_choice.get().split()[-1])
        if self.cap: self.cap.release()
        self.cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        self._loop()

    def _loop(self):
        if self.cap and self.cap.isOpened():
            ok, frame = self.cap.read()
            if ok:
                self.last_frame = frame
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = ctk.CTkImage(Image.fromarray(rgb), size=(480,360))
                self.preview.configure(image=img, text="")
        self.after(30, self._loop)

    def capture(self):
        if not getattr(self, "last_frame", None): return
        DATA.joinpath("photos").mkdir(parents=True, exist_ok=True)
        p = DATA / "photos" / f"tmp_{int(time.time()*1000)}.jpg"
        cv2.imwrite(str(p), self.last_frame)
        self.photo_path = str(p)
        self._live_validate()

    def _gather(self):
        g = {k: e.get().strip() for k,e in self.entries.items()}
        g["id_type"] = self.id_type.get()
        g["officer_permission"] = self.perm.get()
        g["photo_path"] = self.photo_path
        return g

    def _live_validate(self, *_):
        errs = validate_visitor(self._gather())
        for k, lbl in self.errors.items():
            lbl.configure(text=errs.get(k, ""))

    def _autofill_mobile(self, _):
        m = self.entries["mobile"].get()
        if len(m) != 10 or not m.isdigit(): return
        prev = self.db.find_last_visit_by_mobile(m)
        if not prev: return
        for k in ("name","email","address","whom_to_meet","purpose","id_number"):
            self.entries[k].delete(0,"end"); self.entries[k].insert(0, prev.get(k) or "")
        if prev.get("id_type") in self.id_type.cget("values"):
            self.id_type.set(prev["id_type"])

    def submit(self):
        g = self._gather()
        errs = validate_visitor(g)
        if errs:
            messagebox.showerror("Validation", "\n".join(errs.values())); return
        g.pop("photo_path")
        v = self.db.add_visitor(g)
        final_photo = DATA / "photos" / f"{v['visitor_number'].replace('/','-')}.jpg"
        Path(self.photo_path).rename(final_photo)
        # update photo path
        with self.db.lock, self.db.conn:
            self.db.conn.execute("UPDATE visitors SET photo_path=? WHERE id=?",
                                 (str(final_photo), v["id"]))
        v = self.db.get_visitor(v["id"])
        pdf = DATA / "passes" / f"{v['visitor_number'].replace('/','-')}.pdf"
        generate_pass(v, pdf)
        messagebox.showinfo("Saved", f"Visitor {v['visitor_number']} saved.\nPass: {pdf}")
        self.app.show_view("dashboard")
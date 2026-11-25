import sys
from pathlib import Path
import sys
from pathlib import Path
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent

DATA = BASE_DIR / "data"
DATA.mkdir(exist_ok=True)
import customtkinter as ctk
from tkinter import messagebox

from core.database import Database
from core.verify_license import load_license
from core.feature_management import bootstrap_features, allowed_features
from ui.login import LoginDialog
from ui.dashboard import Dashboard
from ui.add_visitor import AddVisitor
from ui.checkout_visitor import CheckoutVisitor
from ui.view_visitors import ViewVisitors
from ui.parcel_management import ParcelManagement
from ui.feature_selection_dialog import FeatureSelectionDialog


if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent

DATA = BASE_DIR / "data"
DATA.mkdir(exist_ok=True) 

ctk.set_appearance_mode("light")


class App(ctk.CTk):
    def __init__(self, license_payload):
        super().__init__()
        self.payload = license_payload
        
       
        client_name = license_payload.get('client_name', 'Unknown Client')
        self.title(f"Visitor Management — {client_name}")
        self.geometry("1200x720")
        self.minsize(1000, 600)
        
       
        self.db = Database(DATA / "visitors.db", client_name)
        bootstrap_features(self.db, license_payload)

        
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(side="right", fill="both", expand=True)
        
        
        self.views = {
            "dashboard": ("Dashboard", lambda: Dashboard(self.content, self.db, self)),
            "add":       ("Add Visitor", lambda: AddVisitor(self.content, self.db, self)),
            "checkout":  ("Checkout", lambda: CheckoutVisitor(self.content, self.db, self)),
            "view":      ("View Visitors", lambda: ViewVisitors(self.content, self.db, self)),
        }
        
        if self.db.feature_enabled("parcels"):
            self.views["parcels"] = ("Parcels", lambda: ParcelManagement(self.content, self.db, self))
            
        self._build_sidebar()
        self.show_view("dashboard")

    def _build_sidebar(self):
       
        for w in self.sidebar.winfo_children(): 
            w.destroy()
            
        ctk.CTkLabel(self.sidebar, text="DGGI VMS", font=("", 20, "bold")).pack(pady=20)
        

        for key, (label, _) in self.views.items():
            ctk.CTkButton(self.sidebar, text=label,
                          command=lambda k=key: self.show_view(k)).pack(fill="x", pady=3, padx=8)
                          
       
        if self.db.feature_enabled("backup"):
            ctk.CTkButton(self.sidebar, text="Backup now", command=self._backup).pack(
                fill="x", side="bottom", pady=8, padx=8)

    def show_view(self, key):
       
        for w in self.content.winfo_children(): 
            w.destroy()
            
        if key not in self.views:
            messagebox.showerror("Error", f"View '{key}' is not available.")
            return
            
       
        _,factory = self.views[key]
        factory().pack(fill="both", expand=True)

    def _backup(self):
        from core.drive_backup import backup_to_drive
        try:
            print("Backup process started...")
            res = backup_to_drive(DATA)
            messagebox.showinfo("Backup", f"Backup uploaded successfully!\n{res}")
        except Exception as e:
            messagebox.showerror("Backup Error", str(e))


def start():
   
    root = ctk.CTk()
    root.withdraw() 
    
    payload = load_license()
    if payload is None:
    
        messagebox.showerror("License Error", "Missing or invalid license file.\nPlease place license.lic in C:\\ProgramData\\VisitorManagement\\")
        root.destroy()
        return
        
    def after_login():
        root.destroy()
        app = App(payload)
        if not app.db.get_features():
            FeatureSelectionDialog(app, allowed_features(payload),
                lambda chosen: (bootstrap_features(app.db, payload, chosen),
                                app._build_sidebar()))
        app.mainloop()
        
    LoginDialog(root, after_login)
    root.mainloop()


if __name__ == "__main__":
    start()
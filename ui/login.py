import customtkinter as ctk

class LoginDialog(ctk.CTkToplevel):
    def __init__(self, master, on_ok):
        super().__init__(master)
        self.on_ok = on_ok
        self.title("Login"); self.geometry("340x220"); self.grab_set()
        ctk.CTkLabel(self, text="Reception Login", font=("", 18, "bold")).pack(pady=15)
        self.user = ctk.CTkEntry(self, placeholder_text="User ID"); self.user.pack(pady=5)
        self.pw = ctk.CTkEntry(self, placeholder_text="Password", show="*"); self.pw.pack(pady=5)
        self.err = ctk.CTkLabel(self, text="", text_color="red"); self.err.pack()
        ctk.CTkButton(self, text="Login", command=self._check).pack(pady=10)

    def _check(self):
        if self.user.get() == "admin" and self.pw.get() == "admin":
            self.destroy(); self.on_ok()
        else:
            self.err.configure(text="Invalid credentials")
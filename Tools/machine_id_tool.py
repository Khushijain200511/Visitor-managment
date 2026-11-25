from core.machine_id import get_machine_id
import tkinter as tk
r = tk.Tk(); r.title("Machine ID"); r.geometry("500x140")
mid = get_machine_id()
tk.Label(r, text="Send this ID to your vendor:", font=("", 12)).pack(pady=8)
e = tk.Entry(r, width=70); e.insert(0, mid); e.pack()
tk.Button(r, text="Copy", command=lambda: (r.clipboard_clear(),
         r.clipboard_append(mid))).pack(pady=8)
r.mainloop()
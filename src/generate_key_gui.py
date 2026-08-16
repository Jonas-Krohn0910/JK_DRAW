import tkinter as tk
from tkinter import ttk

from license.keygen import generate_key


class KeyGeneratorApp:
    def __init__(self, root):
        self.root = root
        root.title("JK Draw - Nøgle generering")
        root.resizable(False, False)

        frame = ttk.Frame(root, padding=20)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text="Hardware-ID fra kunden:", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )
        self.hw_var = tk.StringVar()
        hw_entry = ttk.Entry(frame, textvariable=self.hw_var, width=45)
        hw_entry.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        hw_entry.focus_set()

        ttk.Button(frame, text="Generér nøgle", command=self.on_generate).grid(
            row=2, column=0, pady=(0, 15)
        )

        ttk.Label(frame, text="Licensnøgle:", font=("Arial", 10, "bold")).grid(
            row=3, column=0, sticky="w", pady=(0, 5)
        )
        self.key_var = tk.StringVar()
        self.key_entry = ttk.Entry(frame, textvariable=self.key_var, width=45, state="readonly")
        self.key_entry.grid(row=4, column=0, sticky="ew", pady=(0, 10))

        ttk.Button(frame, text="Kopiér nøgle", command=self.on_copy).grid(row=5, column=0)

        self.status_var = tk.StringVar(value="")
        self.status_label = ttk.Label(frame, textvariable=self.status_var)
        self.status_label.grid(row=6, column=0, pady=(10, 0))

        hw_entry.bind("<Return>", lambda e: self.on_generate())

    def on_generate(self):
        hw_id = self.hw_var.get().strip().lower()
        if not hw_id:
            self._set_status("Indtast et hardware-ID.", "red")
            return
        try:
            key = generate_key(hw_id)
        except Exception as e:
            self._set_status(f"Fejl: {e}", "red")
            return

        self.key_entry.configure(state="normal")
        self.key_var.set(key)
        self.key_entry.configure(state="readonly")
        self._set_status("Nøgle genereret.", "green")

    def on_copy(self):
        key = self.key_var.get()
        if not key:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(key)
        self._set_status("Kopieret til udklipsholder.", "green")

    def _set_status(self, text, color):
        self.status_var.set(text)
        self.status_label.configure(foreground=color)


if __name__ == "__main__":
    root = tk.Tk()
    app = KeyGeneratorApp(root)
    root.mainloop()

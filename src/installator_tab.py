import tkinter as tk
from tkinter import ttk

from license import get_hardware_id, is_unlocked, unlock_with_key


class InstallatorTab:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self._build()

    # ---------------------------------------------------------
    def _build(self):
        for widget in self.frame.winfo_children():
            widget.destroy()

        if is_unlocked():
            self._build_unlocked_content()
        else:
            self._build_lock_screen()

    # ---------------------------------------------------------
    def _build_lock_screen(self):
        container = ttk.Frame(self.frame)
        container.pack(expand=True, pady=40)

        ttk.Label(
            container, text="🔒 Installatør", font=("Arial", 14, "bold")
        ).pack(pady=(0, 10))

        ttk.Label(
            container,
            text="Denne fane kræver en licensnøgle bundet til denne computer.",
            font=("Arial", 10),
        ).pack(pady=(0, 20))

        hw_frame = ttk.Frame(container)
        hw_frame.pack(pady=(0, 15))
        ttk.Label(hw_frame, text="Hardware-ID:", font=("Arial", 9, "bold")).pack(
            side="left", padx=(0, 5)
        )
        hw_entry = ttk.Entry(hw_frame, width=20, justify="center")
        hw_entry.insert(0, get_hardware_id())
        hw_entry.configure(state="readonly")
        hw_entry.pack(side="left")

        ttk.Label(container, text="Licensnøgle:").pack()

        key_var = tk.StringVar()
        key_entry = ttk.Entry(container, textvariable=key_var, width=45, justify="center")
        key_entry.pack(pady=(0, 10))

        status_var = tk.StringVar(value="")
        ttk.Label(container, textvariable=status_var, foreground="red").pack()

        def try_unlock(event=None):
            key = key_var.get().strip()
            if not key:
                status_var.set("Indtast en licensnøgle.")
                return
            try:
                unlocked = unlock_with_key(key)
            except Exception as e:
                # Under pythonw.exe (ingen konsol) forsvinder en ufanget
                # exception her sporløst for brugeren - vis den i stedet.
                status_var.set(f"Fejl: {e}")
                return
            if unlocked:
                self._build()
            else:
                status_var.set("Ugyldig licensnøgle for denne computer.")

        ttk.Button(container, text="Lås op", command=try_unlock).pack(pady=5)
        key_entry.bind("<Return>", try_unlock)
        key_entry.focus_set()

    # ---------------------------------------------------------
    def _build_unlocked_content(self):
        ttk.Label(
            self.frame,
            text="Installatør-værktøj kommer snart.",
            font=("Arial", 12),
        ).pack(expand=True, pady=40)

import tkinter as tk
from tkinter import ttk
from vector_tab import VectorTab
from help_tab import HelpTab
from funktionsfit import Funktionsfit
from funktionstegner import Funktionstegner
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
from updater_checker import check_for_updates



class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vektorværktøj")

        # Top-bar med opdateringsknap
        self.top_frame = ttk.Frame(root)
        self.top_frame.pack(fill="x")

        update_button = ttk.Button(self.top_frame, text="Søg efter opdateringer",
                                   command=lambda: check_for_updates(show_popup=True))
        update_button.pack(side="right", padx=10)

        # Notebook med faner
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)

        self.vector_tab = VectorTab(self.notebook)
        self.notebook.add(self.vector_tab.frame, text="Vektorværktøj")

        self.linreg_tab = Funktionsfit(self.notebook)
        self.notebook.add(self.linreg_tab.frame, text="Funktionsfit")

        self.funktion_tab = Funktionstegner(self.notebook)
        self.notebook.add(self.funktion_tab.frame, text="Funktionstegner")

        self.help_tab = HelpTab(self.notebook)
        self.notebook.add(self.help_tab.frame, text="Hjælp")

        # Footer (copyright)
        footer = tk.Label(
            root,
            text="© 2026 Jonas Krohn monkey",
            font=("Arial", 8),
            fg="gray"
        )
        footer.pack(side="bottom", pady=3)

        # Fang lukning af vinduet
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.root.quit()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()



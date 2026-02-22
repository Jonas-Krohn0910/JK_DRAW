import tkinter as tk
from tkinter import ttk
from vector_tab import VectorTab
from help_tab import HelpTab
from funktionsfit import Funktionsfit
from funktionstegner import Funktionstegner
import sys
import os

# Find projektroden (mappen over src)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from update_checker import check_for_updates


# ---------------------------------------------------------
# ScrollableFrame – kan bruges til ALLE faner
# ---------------------------------------------------------
class ScrollableFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


# ---------------------------------------------------------
# Main Application
# ---------------------------------------------------------
class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vektorværktøj")

        # Top-bar
        self.top_frame = ttk.Frame(root)
        self.top_frame.pack(fill="x")

        update_button = ttk.Button(
            self.top_frame,
            text="Søg efter opdateringer",
            command=lambda: check_for_updates(show_popup=True)
        )
        update_button.pack(side="right", padx=10)

        # Notebook
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)

        # -------------------------
        # Vektorværktøj (scroll)
        # -------------------------
        vector_scroll = ScrollableFrame(self.notebook)
        self.vector_tab = VectorTab(vector_scroll.scrollable_frame)
        self.vector_tab.frame.pack(fill="both", expand=True)
        self.notebook.add(vector_scroll, text="Vektorværktøj")

        # -------------------------
        # Funktionsfit (scroll)
        # -------------------------
        linreg_scroll = ScrollableFrame(self.notebook)
        self.linreg_tab = Funktionsfit(linreg_scroll.scrollable_frame)
        self.linreg_tab.frame.pack(fill="both", expand=True)
        self.notebook.add(linreg_scroll, text="Funktionsfit")

        # -------------------------
        # Funktionstegner (scroll)
        # -------------------------
        funktion_scroll = ScrollableFrame(self.notebook)
        self.funktion_tab = Funktionstegner(funktion_scroll.scrollable_frame)
        self.funktion_tab.frame.pack(fill="both", expand=True)
        self.notebook.add(funktion_scroll, text="Funktionstegner")

        # -------------------------
        # Hjælp (har allerede scroll)
        # -------------------------
        self.help_tab = HelpTab(self.notebook)
        self.notebook.add(self.help_tab.frame, text="Hjælp")

        # Footer
        footer = tk.Label(
            root,
            text="© 2026 Jonas Krohn",
            font=("Arial", 8),
            fg="gray"
        )
        footer.pack(side="bottom", pady=3)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.root.quit()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()

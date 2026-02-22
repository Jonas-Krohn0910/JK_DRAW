import tkinter as tk
from tkinter import ttk
import os

class HelpTab:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)

        # Notebook (faner)
        notebook = ttk.Notebook(self.frame)
        notebook.pack(fill="both", expand=True)

        # Mappe med tekstfiler
        help_folder = "help_text"

        # Find alle .txt filer
        for filename in os.listdir(help_folder):
            if filename.endswith(".txt"):
                tab_title = self._format_title(filename)
                filepath = os.path.join(help_folder, filename)
                self._create_help_tab(notebook, tab_title, filepath)

    # ---------- Opret en fane og læs tekstfil ----------
    def _create_help_tab(self, notebook, title, filepath):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=title)

        # Scrollable canvas
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Indlæs tekst
        text = self._load_text(filepath)

        # Vis tekst
        ttk.Label(
            scroll_frame,
            text=text,
            wraplength=700,
            justify="left",
            anchor="nw"
        ).pack(fill="both", expand=True, padx=10, pady=10)

    # ---------- Læs tekstfil ----------
    def _load_text(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except:
            return "Kunne ikke indlæse denne hjælpetekst."

    # ---------- Lav pæne titler ud fra filnavne ----------
    def _format_title(self, filename):
        name = filename.replace(".txt", "")
        name = name.replace("_", " ")
        return name.capitalize()

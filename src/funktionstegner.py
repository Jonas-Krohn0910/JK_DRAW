import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
import tkinter.messagebox as messagebox

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
# JK_DRAW - Engineering Visualization Tool
# Author: Jonas <efternavn hvis du vil>
# Created: 2024
# License: MIT


class Funktionstegner:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)

        # Liste over funktioner
        # hver: {"expr": ..., "lambda": ..., "color": ..., "name": "f(x)", "pretty": "..."}
        self.functions = []

        # ---------- Zoom UI-skalering ----------
        zoom_frame = ttk.LabelFrame(self.frame, text="Zoom / UI-størrelse")
        zoom_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(zoom_frame, text="UI-størrelse:").pack(side="left", padx=5)
        self.zoom_var = tk.StringVar(value="100%")
        zoom_box = ttk.Combobox(
            zoom_frame,
            textvariable=self.zoom_var,
            values=["80%", "100%", "120%", "150%", "180%"],
            width=6,
            state="readonly",
        )
        zoom_box.pack(side="left", padx=5)
        zoom_box.bind("<<ComboboxSelected>>", self.change_ui_scale)

        # ---------- Funktion controller ----------
        ctrl = ttk.LabelFrame(self.frame, text="Funktionstyper")
        ctrl.pack(fill="x", padx=10, pady=10)

        ttk.Button(ctrl, text="Lineær", command=lambda: self.open_param_popup("linear")).pack(side="left", padx=5)
        ttk.Button(ctrl, text="2. grad", command=lambda: self.open_param_popup("quadratic")).pack(side="left", padx=5)
        ttk.Button(ctrl, text="3. grad", command=lambda: self.open_param_popup("cubic")).pack(side="left", padx=5)
        ttk.Button(ctrl, text="4. grad", command=lambda: self.open_param_popup("quartic")).pack(side="left", padx=5)

        ttk.Button(ctrl, text="Eksponentiel", command=lambda: self.open_param_popup("exp")).pack(side="left", padx=5)
        ttk.Button(ctrl, text="Logaritmisk", command=lambda: self.open_param_popup("log")).pack(side="left", padx=5)
        ttk.Button(ctrl, text="Potens", command=lambda: self.open_param_popup("power")).pack(side="left", padx=5)

        ttk.Button(ctrl, text="sin", command=lambda: self.open_param_popup("sin")).pack(side="left", padx=5)
        ttk.Button(ctrl, text="cos", command=lambda: self.open_param_popup("cos")).pack(side="left", padx=5)

        # ---------- Interval ----------
        interval_frame = ttk.LabelFrame(self.frame, text="Plot-interval")
        interval_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(interval_frame, text="x-min:").pack(side="left")
        self.xmin_entry = ttk.Entry(interval_frame, width=6)
        self.xmin_entry.insert(0, "-10")
        self.xmin_entry.pack(side="left", padx=5)

        ttk.Label(interval_frame, text="x-max:").pack(side="left")
        self.xmax_entry = ttk.Entry(interval_frame, width=6)
        self.xmax_entry.insert(0, "10")
        self.xmax_entry.pack(side="left", padx=5)

        ttk.Label(interval_frame, text="y-min:").pack(side="left")
        self.ymin_entry = ttk.Entry(interval_frame, width=6)
        self.ymin_entry.insert(0, "-10")
        self.ymin_entry.pack(side="left", padx=5)

        ttk.Label(interval_frame, text="y-max:").pack(side="left")
        self.ymax_entry = ttk.Entry(interval_frame, width=6)
        self.ymax_entry.insert(0, "10")
        self.ymax_entry.pack(side="left", padx=5)

        ttk.Button(interval_frame, text="Opdater akser", command=self.update_plot).pack(side="left", padx=10)

        # ---------- Funktion-liste ----------
        list_frame = ttk.LabelFrame(self.frame, text="Funktioner")
        list_frame.pack(fill="x", padx=10, pady=10)

        columns = ("name", "pretty")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=5)
        self.tree.heading("name", text="Navn")
        self.tree.heading("pretty", text="f(x)")
        self.tree.column("name", width=60, anchor="center")
        self.tree.column("pretty", width=320, anchor="w")
        self.tree.pack(side="left", padx=5, pady=5)

        ttk.Button(list_frame, text="Fjern valgt", command=self.remove_function).pack(side="left", padx=10)
        ttk.Button(list_frame, text="Skæringspunkter", command=self.find_intersections).pack(side="left", padx=10)
        ttk.Button(list_frame, text="Akse-skæringer", command=self.find_axis_intersections).pack(side="left", padx=10)
        ttk.Button(list_frame, text="Toppunkt", command=self.find_vertex).pack(side="left", padx=10)

        # ---------- Plot ----------
        plot_frame = ttk.Frame(self.frame)
        plot_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)

        self.toolbar = NavigationToolbar2Tk(self.canvas, plot_frame)
        self.toolbar.update()

        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.ax.set_title("Funktionstegner")
        self.canvas.draw()

    # ---------- UI scaling ----------
    def change_ui_scale(self, event=None):
        scale = self.zoom_var.get().replace("%", "")
        factor = float(scale) / 100

        # Tkinter widget scaling
        self.frame.tk.call("tk", "scaling", factor)

        # Font scaling
        default_font = tkFont.nametofont("TkDefaultFont")
        text_font = tkFont.nametofont("TkTextFont")
        fixed_font = tkFont.nametofont("TkFixedFont")

        for f in (default_font, text_font, fixed_font):
            size = int(10 * factor)
            f.configure(size=size)

        # Matplotlib scaling
        base_width, base_height = 6, 4
        self.fig.set_size_inches(base_width * factor, base_height * factor)
        self.fig.set_dpi(100 * factor)

        self.canvas.draw_idle()
        self.frame.update_idletasks()

    # ---------- Hjælpere: funktionsnavn ----------
    def get_function_name(self, index):
        # f(x), g(x), h(x), ..., z(x)
        if index > (ord("z") - ord("f")):
            return None
        letter = chr(ord("f") + index)
        return f"{letter}(x)"

    # ---------- Hjælpere: formattering ----------
    def format_polynomial_pretty(self, coeffs):
        # coeffs: liste fra højeste grad til laveste
        degree = len(coeffs) - 1
        terms = []
        supers = {2: "²", 3: "³", 4: "⁴"}

        for i, a in enumerate(coeffs):
            power = degree - i
            if abs(a) < 1e-12:
                continue

            sign = "-" if a < 0 else "+"
            val = abs(a)

            if power == 0:
                term = f"{val:g}"
            elif power == 1:
                if abs(val - 1) < 1e-12:
                    term = "x"
                else:
                    term = f"{val:g}x"
            else:
                sup = supers.get(power, f"^{power}")
                if abs(val - 1) < 1e-12:
                    term = f"x{sup}"
                else:
                    term = f"{val:g}x{sup}"

            terms.append((sign, term))

        if not terms:
            return "0"

        first_sign, first_term = terms[0]
        expr = ""
        if first_sign == "-":
            expr += "- " + first_term
        else:
            expr += first_term

        for sign, term in terms[1:]:
            expr += f" {sign} {term}"

        return expr

    def format_exp_pretty(self, a, b):
        return f"{a:g}·e^({b:g}x)"

    def format_log_pretty(self, a, b):
        return f"{a:g}·ln(x) + {b:g}"

    def format_power_pretty(self, a, b):
        return f"{a:g}·x^{b:g}"

    def format_trig_pretty(self, a, b, kind):
        if kind == "sin":
            return f"{a:g}·sin({b:g}x)"
        else:
            return f"{a:g}·cos({b:g}x)"

    # ---------- Pop-up til koefficienter ----------
    def open_param_popup(self, kind):
        if len(self.functions) > (ord("z") - ord("f")):
            messagebox.showerror("Maks antal funktioner", "Du kan ikke tilføje flere funktioner (sidste er z(x)).")
            return

        popup = tk.Toplevel(self.frame)
        popup.transient(self.frame)
        popup.grab_set()

        if kind == "linear":
            popup.title("Lineær funktion: a·x + b")
            coeffs = ["a", "b"]
        elif kind == "quadratic":
            popup.title("2. grads funktion: a·x² + b·x + c")
            coeffs = ["a", "b", "c"]
        elif kind == "cubic":
            popup.title("3. grads funktion: a·x³ + b·x² + c·x + d")
            coeffs = ["a", "b", "c", "d"]
        elif kind == "quartic":
            popup.title("4. grads funktion: a·x⁴ + b·x³ + c·x² + d·x + e")
            coeffs = ["a", "b", "c", "d", "e"]
        elif kind in ("exp", "log", "power", "sin", "cos"):
            popup.title(f"{kind} funktion")
            coeffs = ["a", "b"]
        else:
            popup.destroy()
            return

        entries = {}
        row = 0
        ttk.Label(popup, text="Indtast koefficienter:").grid(row=row, column=0, columnspan=2, padx=10, pady=10)
        row += 1

        for c in coeffs:
            ttk.Label(popup, text=f"{c} =").grid(row=row, column=0, sticky="e", padx=5, pady=5)
            e = ttk.Entry(popup, width=10)
            e.insert(0, "1" if c == "a" else "0")
            e.grid(row=row, column=1, sticky="w", padx=5, pady=5)
            entries[c] = e
            row += 1

        def on_ok():
            try:
                vals = {c: float(entries[c].get()) for c in coeffs}
            except ValueError:
                messagebox.showerror("Fejl", "Alle koefficienter skal være tal.")
                return

            # Byg expr og pretty
            if kind == "linear":
                a, b = vals["a"], vals["b"]
                expr = f"{a}*x + {b}"
                pretty_core = self.format_polynomial_pretty([a, b])
            elif kind == "quadratic":
                a, b, c = vals["a"], vals["b"], vals["c"]
                expr = f"{a}*x**2 + {b}*x + {c}"
                pretty_core = self.format_polynomial_pretty([a, b, c])
            elif kind == "cubic":
                a, b, c, d = vals["a"], vals["b"], vals["c"], vals["d"]
                expr = f"{a}*x**3 + {b}*x**2 + {c}*x + {d}"
                pretty_core = self.format_polynomial_pretty([a, b, c, d])
            elif kind == "quartic":
                a, b, c, d, e = vals["a"], vals["b"], vals["c"], vals["d"], vals["e"]
                expr = f"{a}*x**4 + {b}*x**3 + {c}*x**2 + {d}*x + {e}"
                pretty_core = self.format_polynomial_pretty([a, b, c, d, e])
            elif kind == "exp":
                a, b = vals["a"], vals["b"]
                expr = f"{a}*np.exp({b}*x)"
                pretty_core = self.format_exp_pretty(a, b)
            elif kind == "log":
                a, b = vals["a"], vals["b"]
                expr = f"{a}*np.log(x) + {b}"
                pretty_core = self.format_log_pretty(a, b)
            elif kind == "power":
                a, b = vals["a"], vals["b"]
                expr = f"{a}*x**{b}"
                pretty_core = self.format_power_pretty(a, b)
            elif kind == "sin":
                a, b = vals["a"], vals["b"]
                expr = f"{a}*np.sin({b}*x)"
                pretty_core = self.format_trig_pretty(a, b, "sin")
            elif kind == "cos":
                a, b = vals["a"], vals["b"]
                expr = f"{a}*np.cos({b}*x)"
                pretty_core = self.format_trig_pretty(a, b, "cos")
            else:
                return

            self.add_function_from_expr(expr, pretty_core)
            popup.destroy()

        ttk.Button(popup, text="Tilføj funktion", command=on_ok).grid(
            row=row, column=0, columnspan=2, pady=10
        )

    # ---------- Tilføj funktion fra expr ----------
    def add_function_from_expr(self, expr, pretty_core):
        if len(self.functions) > (ord("z") - ord("f")):
            messagebox.showerror("Maks antal funktioner", "Du kan ikke tilføje flere funktioner (sidste er z(x)).")
            return

        name = self.get_function_name(len(self.functions))
        if name is None:
            messagebox.showerror("Maks antal funktioner", "Du kan ikke tilføje flere funktioner (sidste er z(x)).")
            return

        try:
            func = lambda x: eval(expr, {"__builtins__": {}}, {"x": x, "np": np})
            func(1)
        except Exception:
            messagebox.showerror("Fejl i funktion", "Der opstod en fejl ved evaluering af funktionen.")
            return

        colors = ["red", "blue", "green", "purple", "orange", "brown"]
        color = colors[len(self.functions) % len(colors)]

        pretty_full = f"{name} = {pretty_core}"

        self.functions.append(
            {"expr": expr, "lambda": func, "color": color, "name": name, "pretty": pretty_full}
        )
        self.tree.insert("", "end", values=(name, pretty_full))

        self.update_plot()

    # ---------- Fjern funktion ----------
    def remove_function(self):
        sel = self.tree.selection()
        if not sel:
            return

        index = self.tree.index(sel[0])
        self.tree.delete(sel[0])
        self.functions.pop(index)

        self.update_plot()

    # ---------- Opdater plot ----------
    def update_plot(self):
        try:
            xmin = float(self.xmin_entry.get())
            xmax = float(self.xmax_entry.get())
            ymin = float(self.ymin_entry.get())
            ymax = float(self.ymax_entry.get())
        except ValueError:
            return

        self.ax.clear()

        # Tydelige akser
        self.ax.axhline(0, color="black", linewidth=2)
        self.ax.axvline(0, color="black", linewidth=2)

        self.ax.set_xlim(xmin, xmax)
        self.ax.set_ylim(ymin, ymax)
        self.ax.grid(True)

        x_vals = np.linspace(xmin, xmax, 500)

        for f in self.functions:
            y_vals = f["lambda"](x_vals)
            self.ax.plot(x_vals, y_vals, color=f["color"], label=f["name"])

        if self.functions:
            self.ax.legend()

        self.canvas.draw()

    # ---------- Skæringspunkter ----------
    def find_intersections(self):
        if len(self.functions) < 2:
            return

        xmin = float(self.xmin_entry.get())
        xmax = float(self.xmax_entry.get())

        xs = np.linspace(xmin, xmax, 2000)
        intersections = []

        for i in range(len(self.functions)):
            for j in range(i + 1, len(self.functions)):
                f1 = self.functions[i]["lambda"]
                f2 = self.functions[j]["lambda"]

                y1 = f1(xs)
                y2 = f2(xs)

                diff = y1 - y2
                sign_change = np.where(np.diff(np.sign(diff)))[0]

                for idx in sign_change:
                    x0 = xs[idx]
                    x1 = xs[idx + 1]
                    y0 = diff[idx]
                    y1d = diff[idx + 1]

                    x_inter = x0 - y0 * (x1 - x0) / (y1d - y0)
                    y_inter = f1(x_inter)

                    intersections.append((x_inter, y_inter))

        for x, y in intersections:
            self.ax.plot(x, y, "ko")
            self.ax.text(x, y, f"({x:.2f}, {y:.2f})", fontsize=8)

        self.canvas.draw()

    # ---------- Akse-skæringer ----------
    def find_axis_intersections(self):
        xmin = float(self.xmin_entry.get())
        xmax = float(self.xmax_entry.get())

        xs = np.linspace(xmin, xmax, 2000)

        for f in self.functions:
            func = f["lambda"]

            # Y-akse: x = 0
            try:
                y0 = func(0)
                self.ax.plot(0, y0, "ro")
                self.ax.text(0, y0, f"(0, {y0:.2f})", fontsize=8)
            except Exception:
                pass

            # X-akse: f(x) = 0
            y_vals = func(xs)
            sign_change = np.where(np.diff(np.sign(y_vals)))[0]

            for idx in sign_change:
                x0 = xs[idx]
                x1 = xs[idx + 1]
                y0 = y_vals[idx]
                y1d = y_vals[idx + 1]

                x_inter = x0 - y0 * (x1 - x0) / (y1d - y0)

                self.ax.plot(x_inter, 0, "go")
                self.ax.text(x_inter, 0, f"({x_inter:.2f}, 0)", fontsize=8)

        self.canvas.draw()

    # ---------- Toppunkt ----------
    def find_vertex(self):
        for f in self.functions:
            expr = f["expr"]

            if "x**2" not in expr:
                continue

            xmin = float(self.xmin_entry.get())
            xmax = float(self.xmax_entry.get())
            xs = np.linspace(xmin, xmax, 2000)
            ys = f["lambda"](xs)

            # Vi tager både minimum og maksimum i intervallet
            min_idx = np.argmin(ys)
            max_idx = np.argmax(ys)

            for idx in (min_idx, max_idx):
                xv = xs[idx]
                yv = ys[idx]
                self.ax.plot(xv, yv, "mo")
                self.ax.text(xv, yv, f"({xv:.2f}, {yv:.2f})", fontsize=8)

        self.canvas.draw()

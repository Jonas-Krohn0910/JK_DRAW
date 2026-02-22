import tkinter as tk
from tkinter import ttk, filedialog
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
import numpy as np


class Funktionsfit:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)

        # ---------- Intro ----------
        intro = ttk.Label(
            self.frame,
            text="Importer data og tilpas funktioner (lineær, polynomiel, eksponentiel, logaritmisk, potens).",
            foreground="#444",
            wraplength=600
        )
        intro.pack(pady=(5, 0))

        # ---------- Layout ----------
        top_frame = ttk.LabelFrame(self.frame, text="Indlæs data")
        top_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(top_frame, text="Vælg Excel-fil", command=self.load_excel).pack(side="left", padx=5, pady=5)

        self.file_label = ttk.Label(top_frame, text="Ingen fil valgt")
        self.file_label.pack(side="left", padx=10)

        # ---------- Kolonnevalg ----------
        col_frame = ttk.LabelFrame(self.frame, text="Vælg kolonner")
        col_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(col_frame, text="X-kolonne:").pack(side="left", padx=5)
        self.x_col = ttk.Combobox(col_frame, state="readonly", width=15)
        self.x_col.pack(side="left", padx=5)

        ttk.Label(col_frame, text="Y-kolonne:").pack(side="left", padx=5)
        self.y_col = ttk.Combobox(col_frame, state="readonly", width=15)
        self.y_col.pack(side="left", padx=5)

        # ---------- Regression knapper ----------
        reg_frame = ttk.LabelFrame(self.frame, text="Regressionstyper")
        reg_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(reg_frame, text="Lineær", command=self.run_linear).pack(side="left", padx=5)

        ttk.Label(reg_frame, text="Poly grad:").pack(side="left", padx=5)
        self.poly_degree = ttk.Combobox(reg_frame, values=[2, 3, 4, 5, 6], width=5, state="readonly")
        self.poly_degree.current(0)
        self.poly_degree.pack(side="left", padx=5)

        ttk.Button(reg_frame, text="Polynomiel", command=self.run_poly).pack(side="left", padx=5)
        ttk.Button(reg_frame, text="Eksponentiel", command=self.run_exp).pack(side="left", padx=5)
        ttk.Button(reg_frame, text="Logaritmisk", command=self.run_log).pack(side="left", padx=5)
        ttk.Button(reg_frame, text="Potens", command=self.run_power).pack(side="left", padx=5)

        ttk.Button(reg_frame, text="Ryd plot", command=self.clear_plot).pack(side="right", padx=5)

        # ---------- Resultat ----------
        self.result_label = ttk.Label(self.frame, text="Ingen beregning endnu", justify="left")
        self.result_label.pack(pady=5)

        # ---------- Plot område ----------
        plot_frame = ttk.LabelFrame(self.frame, text="Plot")
        plot_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # ---------- Data ----------
        self.df = None

    # ---------- Indlæs Excel ----------
    def load_excel(self):
        path = filedialog.askopenfilename(
            filetypes=[("Excel filer", "*.xlsx *.xls")]
        )
        if not path:
            return

        try:
            self.df = pd.read_excel(path)

            # Sørg for at alle kolonnenavne er strings
            self.df.columns = (
                self.df.columns
                .map(str)
                .str.strip()
            )

            self.file_label.config(text=f"Indlæst: {path.split('/')[-1]}")

            # Opdater dropdowns
            cols = list(self.df.columns)
            self.x_col["values"] = cols
            self.y_col["values"] = cols

            self.preview_data()
        except Exception as e:
            self.file_label.config(text=f"Fejl: {e}")

    # ---------- Vis preview ----------
    def preview_data(self):
        if self.df is None:
            return

        self.ax.clear()
        self.ax.set_title("Data preview (før regression)")

        if len(self.df.columns) >= 2:
            x = self.df.iloc[:, 0]
            y = self.df.iloc[:, 1]
            self.ax.scatter(x, y, color="blue")
            self.ax.set_xlabel(self.df.columns[0])
            self.ax.set_ylabel(self.df.columns[1])
        else:
            self.ax.text(0.5, 0.5, "Ikke nok kolonner til plot",
                         ha="center", va="center")

        self.canvas.draw()

    # ---------- Hjælpefunktion ----------
    def get_xy(self):
        x_col = self.x_col.get()
        y_col = self.y_col.get()

        if not x_col or not y_col:
            self.result_label.config(text="Vælg X og Y kolonner først")
            return None, None

        x = self.df[x_col].values
        y = self.df[y_col].values
        return x, y

    # ---------- Lineær regression ----------
    def run_linear(self):
        x, y = self.get_xy()
        if x is None:
            return

        x2 = x.reshape(-1, 1)
        model = LinearRegression()
        model.fit(x2, y)

        a = model.coef_[0]
        b = model.intercept_
        r2 = model.score(x2, y)

        # Plot
        self.ax.clear()
        self.ax.scatter(x, y, label="Data")
        self.ax.plot(x, model.predict(x2), color="red", label="Lineær fit")
        self.ax.set_title("Lineær regression")
        self.ax.legend()
        self.canvas.draw()

        self.result_label.config(
            text=f"f(x) = {a:.4f}x + {b:.4f}\nR² = {r2:.4f}"
        )

    # ---------- Polynomiel regression ----------
    def run_poly(self):
        x, y = self.get_xy()
        if x is None:
            return

        degree = int(self.poly_degree.get())
        x2 = x.reshape(-1, 1)

        poly = PolynomialFeatures(degree=degree)
        x_poly = poly.fit_transform(x2)

        model = LinearRegression()
        model.fit(x_poly, y)

        r2 = model.score(x_poly, y)
        coeffs = model.coef_
        intercept = model.intercept_

        # Plot
        x_sorted = np.sort(x)
        y_pred = model.predict(poly.transform(x_sorted.reshape(-1, 1)))

        self.ax.clear()
        self.ax.scatter(x, y, label="Data")
        self.ax.plot(x_sorted, y_pred, color="purple", label=f"Poly grad {degree}")
        self.ax.set_title(f"Polynomiel regression (grad {degree})")
        self.ax.legend()
        self.canvas.draw()

        # Funktionstekst
        func = []
        for i in range(degree, 0, -1):
            func.append(f"{coeffs[i]:.4f}x^{i}")
        func_text = " + ".join(func) + f" + {intercept:.4f}"

        self.result_label.config(text=f"f(x) = {func_text}\nR² = {r2:.4f}")

    # ---------- Eksponentiel regression ----------
    def run_exp(self):
        x, y = self.get_xy()
        if x is None:
            return

        if np.any(y <= 0):
            self.result_label.config(text="Eksponentiel regression kræver y > 0")
            return

        x2 = x.reshape(-1, 1)
        log_y = np.log(y)

        model = LinearRegression()
        model.fit(x2, log_y)

        b = model.coef_[0]
        ln_a = model.intercept_
        a = np.exp(ln_a)
        r2 = model.score(x2, log_y)

        x_sorted = np.sort(x)
        y_pred = a * np.exp(b * x_sorted)

        self.ax.clear()
        self.ax.scatter(x, y, label="Data")
        self.ax.plot(x_sorted, y_pred, color="orange", label="Eksponentiel fit")
        self.ax.set_title("Eksponentiel regression")
        self.ax.legend()
        self.canvas.draw()

        self.result_label.config(text=f"f(x) = {a:.4f}·e^({b:.4f}x)\nR² = {r2:.4f}")

    # ---------- Logaritmisk regression ----------
    def run_log(self):
        x, y = self.get_xy()
        if x is None:
            return

        if np.any(x <= 0):
            self.result_label.config(text="Logaritmisk regression kræver x > 0")
            return

        log_x = np.log(x).reshape(-1, 1)

        model = LinearRegression()
        model.fit(log_x, y)

        a = model.coef_[0]
        b = model.intercept_
        r2 = model.score(log_x, y)

        x_sorted = np.sort(x)
        y_pred = a * np.log(x_sorted) + b

        self.ax.clear()
        self.ax.scatter(x, y, label="Data")
        self.ax.plot(x_sorted, y_pred, color="brown", label="Logaritmisk fit")
        self.ax.set_title("Logaritmisk regression")
        self.ax.legend()
        self.canvas.draw()

        self.result_label.config(text=f"f(x) = {a:.4f} ln(x) + {b:.4f}\nR² = {r2:.4f}")

    # ---------- Potensfunktion ----------
    def run_power(self):
        x, y = self.get_xy()
        if x is None:
            return

        if np.any(x <= 0) or np.any(y <= 0):
            self.result_label.config(text="Potensfunktion kræver x > 0 og y > 0")
            return

        log_x = np.log(x).reshape(-1, 1)
        log_y = np.log(y)

        model = LinearRegression()
        model.fit(log_x, log_y)

        b = model.coef_[0]
        ln_a = model.intercept_
        a = np.exp(ln_a)
        r2 = model.score(log_x, log_y)

        x_sorted = np.sort(x)
        y_pred = a * x_sorted**b

        self.ax.clear()
        self.ax.scatter(x, y, label="Data")
        self.ax.plot(x_sorted, y_pred, color="green", label="Potensfunktion fit")
        self.ax.set_title("Potensfunktion")
        self.ax.legend()
        self.canvas.draw()

        self.result_label.config(text=f"f(x) = {a:.4f} x^{b:.4f}\nR² = {r2:.4f}")

    # ---------- Ryd plot ----------
    def clear_plot(self):
        self.ax.clear()
        self.ax.set_title("Plot ryddet")
        self.canvas.draw()
        self.result_label.config(text="Plot ryddet – vælg en funktion for at fortsætte.")

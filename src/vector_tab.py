import tkinter as tk
from tkinter import ttk, filedialog
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.patches import FancyArrowPatch, Arc
# JK_DRAW - Engineering Visualization Tool
# Author: Jonas <efternavn hvis du vil>
# Created: 2024
# License: MIT

GRID_STEP = 0.2
POINT_SIZE = 10

def pol2cart_horizontal(length, angle_deg):
    angle_rad = np.radians(angle_deg)
    return length * np.cos(angle_rad), length * np.sin(angle_rad)

def pol2cart_vertical(length, angle_deg):
    angle_rad = np.radians(angle_deg)
    return length * np.sin(angle_rad), length * np.cos(angle_rad)


class VectorTab:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)

        # ---------- Plot ----------
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.ax.set_aspect("equal", adjustable="box")
        self.ax.grid(True)
        self.ax.set_xlim(-10, 30)
        self.ax.set_ylim(-10, 10)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, columnspan=3, padx=5, pady=5)

        self.toolbar_frame = ttk.Frame(self.frame)
        self.toolbar_frame.grid(row=1, column=0, columnspan=3, sticky="w")
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        self.toolbar.update()

        # ---------- Venstre panel ----------
        settings_frame = ttk.LabelFrame(self.frame, text="Vektor indstillinger")
        settings_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nw")

        ttk.Label(settings_frame, text="Længde:").grid(row=0, column=0, sticky="e")
        self.length_var = tk.DoubleVar(value=5.0)
        ttk.Entry(settings_frame, textvariable=self.length_var, width=8).grid(row=0, column=1)

        ttk.Label(settings_frame, text="Vinkel (°):").grid(row=1, column=0, sticky="e")
        self.angle_var = tk.DoubleVar(value=30.0)
        ttk.Entry(settings_frame, textvariable=self.angle_var, width=8).grid(row=1, column=1)

        ttk.Label(settings_frame, text="Farve:").grid(row=2, column=0, sticky="e")
        self.color_var = tk.StringVar(value="blue")
        ttk.Combobox(settings_frame, textvariable=self.color_var,
                     values=["blue", "red", "green", "orange", "black"],
                     width=10, state="readonly").grid(row=2, column=1)

        ttk.Label(settings_frame, text="Linjetype:").grid(row=3, column=0, sticky="e")
        self.style_var = tk.StringVar(value="solid")
        ttk.Combobox(settings_frame, textvariable=self.style_var,
                     values=["solid", "dashed", "dotted", "dashdot"],
                     width=12, state="readonly").grid(row=3, column=1)

        ttk.Label(settings_frame, text="Reference:").grid(row=4, column=0, sticky="e")
        self.ref_var = tk.StringVar(value="Standard")
        self.ref_selector = ttk.Combobox(settings_frame, textvariable=self.ref_var,
                                         values=["Standard"],
                                         width=22, state="readonly")
        self.ref_selector.grid(row=4, column=1)

        ttk.Label(settings_frame, text="Startpunkt:").grid(row=5, column=0, sticky="e")
        self.start_mode = tk.StringVar(value="origin")
        self.start_selector = ttk.Combobox(settings_frame, textvariable=self.start_mode,
                                           values=["origin"], width=22, state="readonly")
        self.start_selector.grid(row=5, column=1)

        ttk.Label(settings_frame, text="Navn:").grid(row=6, column=0, sticky="e")
        self.name_var = tk.StringVar(value="")
        ttk.Entry(settings_frame, textvariable=self.name_var, width=12).grid(row=6, column=1)

        ttk.Button(settings_frame, text="Tilføj vektor", command=self.add_vector).grid(row=7, column=0, columnspan=2, pady=5)
        ttk.Button(settings_frame, text="Opret punkt", command=self.enable_point_creation).grid(row=8, column=0, columnspan=2, pady=5)
        ttk.Button(settings_frame, text="Opret reference-linje", command=self.create_reference_line).grid(row=9, column=0, columnspan=2, pady=5)
        # ---------- Midterpanel ----------
        file_frame = ttk.LabelFrame(self.frame, text="Fil")
        file_frame.grid(row=2, column=1, padx=10, pady=10, sticky="nw")

        ttk.Button(file_frame, text="Gem projekt", command=self.save_project).grid(row=0, column=0, pady=5)
        ttk.Button(file_frame, text="Åbn projekt", command=self.load_project).grid(row=1, column=0, pady=5)
        ttk.Button(file_frame, text="Ryd alt", command=self.clear_plot).grid(row=2, column=0, pady=5)

        self.show_points = tk.BooleanVar(value=True)
        ttk.Checkbutton(file_frame, text="Vis punkter", variable=self.show_points,
                        command=self.redraw_plot).grid(row=3, column=0, pady=5)

        self.show_names = tk.BooleanVar(value=True)
        ttk.Checkbutton(file_frame, text="Vis navne", variable=self.show_names,
                        command=self.redraw_plot).grid(row=4, column=0, pady=5)

        zoom_frame = ttk.LabelFrame(file_frame, text="Zoom")
        zoom_frame.grid(row=5, column=0, pady=10)
        self.ui_scale = 1.0
        ttk.Button(zoom_frame, text="-", command=self.zoom_out).grid(row=0, column=0)
        self.zoom_label = ttk.Label(zoom_frame, text="100%")
        self.zoom_label.grid(row=0, column=1, padx=5)
        ttk.Button(zoom_frame, text="+", command=self.zoom_in).grid(row=0, column=2)

        # ---------- Højre panel ----------
        list_frame = ttk.LabelFrame(self.frame, text="Punkter og vektorer")
        list_frame.grid(row=2, column=2, padx=10, pady=10, sticky="n")
        list_frame.columnconfigure(0, weight=0)
        list_frame.columnconfigure(1, weight=0)


        columns = ("type", "name", "x1", "y1", "x2", "y2", "length", "angle", "color", "style")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=18)
        self.tree.grid(row=0, column=0, padx=5, pady=5)

        headers = ["Type", "Navn", "X1", "Y1", "X2", "Y2", "Længde", "Vinkel (°)", "Farve", "Linje"]
        for col, text in zip(columns, headers):
            self.tree.heading(col, text=text)

        for col, w in zip(columns, (70, 80, 60, 60, 60, 60, 70, 70, 70, 70)):
            self.tree.column(col, width=w, anchor="center")

        # Knap-ramme under Treeview
        button_frame = ttk.Frame(list_frame)
        button_frame.grid(row=1, column=0, pady=10)

        ttk.Button(button_frame, text="Fjern valgt",
                command=self.remove_selected_item).grid(row=0, column=0, padx=5, pady=5)

        ttk.Button(button_frame, text="Vektorsum",
                command=self.create_vector_sum).grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(button_frame, text="Vektorforskel",
                command=self.create_vector_difference).grid(row=0, column=2, padx=5, pady=5)

        ttk.Button(button_frame, text="Resultant",
                command=self.create_resultant_vector).grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Vinkel mellem",
           command=self.create_angle_between).grid(row=0, column=4, padx=5, pady=5)



        # ---------- Data ----------
        self.vectors = []
        self.points = []
        self.references = []
        self.angles = []
        self.text_objects = []
        self.point_objects = []
        self.dragging_vector_label = None
        self.dragging_point = None
        self.point_creation_mode = False

        self.item_map = {}
        self.edit_state = None
        self.last_selected = []

        # ---------- Mouse events ----------
        self.fig.canvas.mpl_connect("pick_event", self.on_pick)
        self.fig.canvas.mpl_connect("motion_notify_event", self.on_drag)
        self.fig.canvas.mpl_connect("button_release_event", self.on_release)
        self.fig.canvas.mpl_connect("button_press_event", self.on_click)

        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self.last_selected = []
        self.tree.bind("<ButtonRelease-1>", self.on_tree_select)
        self.tree.bind("<Button-1>", self.tree_click_blocker, add="+")
        self.frame.bind("<Button-1>", self.on_global_click)

    # ---------- Punkt-oprettelse ----------
    def enable_point_creation(self):
        self.point_creation_mode = True

    def on_click(self, event):
        if not self.point_creation_mode:
            return
        if event.xdata is None or event.ydata is None:
            return

        x = round(event.xdata / GRID_STEP) * GRID_STEP
        y = round(event.ydata / GRID_STEP) * GRID_STEP

        name = f"P{len(self.points) + 1}"
        self.points.append((x, y, name))

        self.point_creation_mode = False
        self.update_start_selector()
        self.update_tree()
        self.redraw_plot()
    # ---------- Flytbare punkter og navne ----------
    def on_pick(self, event):
        artist = event.artist

        if artist in self.point_objects:
            self.dragging_point = self.point_objects.index(artist)
            return

        if artist in self.text_objects:
            self.dragging_vector_label = self.text_objects.index(artist)
            return

    def on_drag(self, event):
        if event.xdata is None or event.ydata is None:
            return

        # Flyt punkt
        if self.dragging_point is not None and self.dragging_point < len(self.points):
            x, y, name = self.points[self.dragging_point]
            new_x = round(event.xdata / GRID_STEP) * GRID_STEP
            new_y = round(event.ydata / GRID_STEP) * GRID_STEP
            self.points[self.dragging_point] = (new_x, new_y, name)

            # Flyt vektorer der starter i punktet
            for i, v in enumerate(self.vectors):
                sx, sy, ex, ey, color, vname, dx, dy, style = v
                if sx == x and sy == y:
                    dxv = ex - sx
                    dyv = ey - sy
                    self.vectors[i] = (new_x, new_y, new_x + dxv, new_y + dyv,
                                       color, vname, dx, dy, style)

            self.update_tree()
            self.redraw_plot()
            return

        # Flyt vektor-label
        if self.dragging_vector_label is not None:
            sx, sy, ex, ey, color, name, dx, dy, style = self.vectors[self.dragging_vector_label]
            new_dx = round((event.xdata - ex) / GRID_STEP) * GRID_STEP
            new_dy = round((event.ydata - ey) / GRID_STEP) * GRID_STEP
            self.vectors[self.dragging_vector_label] = (sx, sy, ex, ey, color, name,
                                                        new_dx, new_dy, style)
            self.redraw_plot()

    def on_release(self, event):
        self.dragging_point = None
        self.dragging_vector_label = None

    # ---------- Tilføj vektor ----------
    def add_vector(self):
        length = self.length_var.get()
        angle = self.angle_var.get()
        color = self.color_var.get()
        style = self.style_var.get()
        name = self.name_var.get().strip()

        # Reference-vinkel
        ref = self.ref_var.get()
        if ref == "Standard":
            base_angle = 0.0
        else:
            try:
                idx = int(ref.split("#")[1].split()[0])
                sxr, syr, exr, eyr, ref_angle, rname = self.references[idx]
                base_angle = np.radians(ref_angle)
            except (IndexError, ValueError):
                base_angle = 0.0

        total_angle = base_angle + np.radians(angle)
        dx = length * np.cos(total_angle)
        dy = length * np.sin(total_angle)

        # Startpunkt
        mode = self.start_mode.get()

        if mode == "origin":
            sx, sy = 0, 0

        elif mode.startswith("point #"):
            idx = int(mode.split("#")[1].split()[0])
            sx, sy, pname = self.points[idx]

        elif mode.startswith("vector #"):
            idx = int(mode.split("#")[1].split()[0])
            sx, sy, ex, ey, c, n, ldx, ldy, st = self.vectors[idx]
            sx, sy = ex, ey

        else:
            sx, sy = 0, 0

        ex, ey = sx + dx, sy + dy

        # Label offset
        label_dx = 0.2
        label_dy = 0.2

        self.vectors.append((sx, sy, ex, ey, color, name, label_dx, label_dy, style))
        self.update_tree()
        self.update_start_selector()
        self.redraw_plot()

    # ---------- Fjern punkt/vektor/reference ----------
    def remove_selected_item(self):
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]
        if item not in self.item_map:
            return

        kind, idx = self.item_map[item]

        if kind == "point":
            if 0 <= idx < len(self.points):
                self.points.pop(idx)

        elif kind == "vector":
            if 0 <= idx < len(self.vectors):
                self.vectors.pop(idx)

        elif kind == "reference":
            if 0 <= idx < len(self.references):
                self.references.pop(idx)
        elif kind == "angle":
            if 0 <= idx < len(self.angles):
                self.angles.pop(idx)

        self.update_tree()
        self.update_start_selector()
        self.update_reference_selector()
        self.redraw_plot()
    # ---------- Inline-redigering ----------
    def tree_click_blocker(self, event):
        if self.edit_state is not None:
            return "break"

    def on_tree_double_click(self, event):
        # Blokér nye redigeringer hvis én allerede er aktiv
        if self.edit_state is not None:
            return

        item = self.tree.identify_row(event.y)
        if not item or item not in self.item_map:
            return

        kind, idx = self.item_map[item]
        # ---------- REFERENCE-REDIGERING ----------
        if kind == "reference":
            sx, sy, ex, ey, angle, name = self.references[idx]

            b_name = self.tree.bbox(item, "name")
            b_length = self.tree.bbox(item, "length")

            def make_entry(bbox, initial):
                e = tk.Entry(self.tree)
                e.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
                e.insert(0, initial)
                return e

            e_name = make_entry(b_name, name)
            length = ((ex - sx)**2 + (ey - sy)**2)**0.5
            e_length = make_entry(b_length, f"{length:.2f}")

            self.edit_state = {
                "type": "reference",
                "item": item,
                "idx": idx,
                "e_name": e_name,
                "e_length": e_length
            }

            for e in (e_name, e_length):
                e.bind("<Return>", self.commit_reference_edit)

            e_name.focus_set()
            return


        # ---------- PUNKT-REDIGERING ----------
        if kind == "point":
            x, y, name = self.points[idx]

            bbox_name = self.tree.bbox(item, "name")
            bbox_x1 = self.tree.bbox(item, "x1")
            bbox_y1 = self.tree.bbox(item, "y1")
            if not bbox_name or not bbox_x1 or not bbox_y1:
                return

            def make_entry(bbox, initial):
                e = tk.Entry(self.tree)
                e.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
                e.insert(0, initial)
                return e

            e_name = make_entry(bbox_name, name)
            e_x = make_entry(bbox_x1, f"{x:.2f}")
            e_y = make_entry(bbox_y1, f"{y:.2f}")

            self.edit_state = {
                "type": "point",
                "item": item,
                "idx": idx,
                "old_x": x,
                "old_y": y,
                "e_name": e_name,
                "e_x": e_x,
                "e_y": e_y
            }
            self.tree.selection_set(item)

            for e in (e_name, e_x, e_y):
                e.bind("<Return>", self.commit_point_edit)

            e_name.focus_set()
            return

        # ---------- VEKTOR-REDIGERING ----------
        if kind == "vector":
            sx, sy, ex, ey, color, name, dx, dy, style = self.vectors[idx]

            # Hent bounding boxes
            b_name = self.tree.bbox(item, "name")
            b_x1 = self.tree.bbox(item, "x1")
            b_y1 = self.tree.bbox(item, "y1")
            b_x2 = self.tree.bbox(item, "x2")
            b_y2 = self.tree.bbox(item, "y2")
            b_color = self.tree.bbox(item, "color")
            b_style = self.tree.bbox(item, "style")

            def make_entry(bbox, initial):
                e = tk.Entry(self.tree)
                e.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
                e.insert(0, initial)
                return e

            def make_combo(bbox, values, initial):
                cb = ttk.Combobox(self.tree, values=values, state="readonly")
                cb.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
                cb.set(initial)
                return cb

            e_name = make_entry(b_name, name)
            e_x1 = make_entry(b_x1, f"{sx:.2f}")
            e_y1 = make_entry(b_y1, f"{sy:.2f}")
            e_x2 = make_entry(b_x2, f"{ex:.2f}")
            e_y2 = make_entry(b_y2, f"{ey:.2f}")

            e_color = make_combo(b_color,
                                 ["blue", "red", "green", "orange", "black"],
                                 color)

            e_style = make_combo(b_style,
                                 ["solid", "dashed", "dotted", "dashdot"],
                                 style)

            self.edit_state = {
                "type": "vector",
                "item": item,
                "idx": idx,
                "e_name": e_name,
                "e_x1": e_x1,
                "e_y1": e_y1,
                "e_x2": e_x2,
                "e_y2": e_y2,
                "e_color": e_color,
                "e_style": e_style
            }
            self.tree.selection_set(item)

            for e in (e_name, e_x1, e_y1, e_x2, e_y2, e_color, e_style):
                e.bind("<Return>", self.commit_vector_edit)

            e_name.focus_set()
    
    def on_tree_select(self, event):
        # Find det item musen klikkede på
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return

        # Fjern ID'er der ikke længere findes
        valid_items = set(self.tree.get_children())
        self.last_selected = [item for item in self.last_selected if item in valid_items]

        # Tilføj sidst klikkede item
        if not self.last_selected or self.last_selected[-1] != row_id:
            self.last_selected.append(row_id)

        # Hold kun de sidste to
        if len(self.last_selected) > 2:
            self.last_selected.pop(0)


    # ---------- Global klik ----------
    def on_global_click(self, event):
        return
    # ---------- Commit punkt-redigering ----------
    def commit_point_edit(self, event):
        if self.edit_state is None or self.edit_state["type"] != "point":
            return

        idx = self.edit_state["idx"]
        old_x = self.edit_state["old_x"]
        old_y = self.edit_state["old_y"]

        e_name = self.edit_state["e_name"]
        e_x = self.edit_state["e_x"]
        e_y = self.edit_state["e_y"]

        try:
            new_name = e_name.get().strip()
            new_x = float(e_x.get().replace(",", "."))
            new_y = float(e_y.get().replace(",", "."))
        except ValueError:
            new_name = self.points[idx][2]
            new_x = self.points[idx][0]
            new_y = self.points[idx][1]

        self.points[idx] = (new_x, new_y, new_name)

        # Flyt vektorer der starter i punktet
        for i, v in enumerate(self.vectors):
            sx, sy, ex, ey, color, vname, dx, dy, style = v
            if sx == old_x and sy == old_y:
                dxv = ex - sx
                dyv = ey - sy
                self.vectors[i] = (new_x, new_y, new_x + dxv, new_y + dyv,
                                   color, vname, dx, dy, style)

        for e in (e_name, e_x, e_y):
            e.destroy()

        self.edit_state = None
        self.update_tree()
        self.update_start_selector()
        self.redraw_plot()

    # ---------- Commit vektor-redigering ----------
    def commit_vector_edit(self, event):
        if self.edit_state is None or self.edit_state["type"] != "vector":
            return

        st = self.edit_state
        idx = st["idx"]

        try:
            name = st["e_name"].get().strip()
            sx = float(st["e_x1"].get().replace(",", "."))
            sy = float(st["e_y1"].get().replace(",", "."))
            ex = float(st["e_x2"].get().replace(",", "."))
            ey = float(st["e_y2"].get().replace(",", "."))
            color = st["e_color"].get()
            style = st["e_style"].get()
        except ValueError:
            sx, sy, ex, ey, color, name, dx, dy, style = self.vectors[idx]

        old = self.vectors[idx]
        dx, dy = old[6], old[7]

        self.vectors[idx] = (sx, sy, ex, ey, color, name, dx, dy, style)

        for key in st:
            if key.startswith("e_"):
                st[key].destroy()

        self.edit_state = None
        self.update_tree()
        self.update_start_selector()
        self.redraw_plot()
    # ---------- Commit reference edit ----------
    def commit_reference_edit(self, event):
        st = self.edit_state
        idx = st["idx"]

        sx, sy, ex_old, ey_old, angle, old_name = self.references[idx]

        try:
            name = st["e_name"].get().strip()
            new_length = float(st["e_length"].get().replace(",", "."))
        except ValueError:
            name = old_name
            new_length = ((ex_old - sx)**2 + (ey_old - sy)**2)**0.5

        # Beregn nye koordinater ud fra længde og vinkel
        rad = np.radians(angle)
        ex = sx + new_length * np.cos(rad)
        ey = sy + new_length * np.sin(rad)

        # Opdater reference-linje
        self.references[idx] = (sx, sy, ex, ey, angle, name)

        # Ryd editor-widgets
        for key in st:
            if key.startswith("e_"):
                st[key].destroy()

        self.edit_state = None
        self.update_tree()
        self.update_reference_selector() 
        self.redraw_plot()


    # ---------- Save/Load ----------
    def save_project(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt")
        if not path:
            return
        with open(path, "w") as f:
            for p in self.points:
                f.write(f"POINT {p[0]} {p[1]} {p[2]}\n")
            for v in self.vectors:
                f.write("VECTOR " + " ".join(map(str, v)) + "\n")
            # Reference-linjer gemmes ikke i denne version

    def load_project(self):
        path = filedialog.askopenfilename()
        if not path:
            return

        self.points = []
        self.vectors = []
        self.references = []

        with open(path, "r") as f:
            for line in f:
                parts = line.split()
                if parts[0] == "POINT":
                    _, x, y, name = parts
                    self.points.append((float(x), float(y), name))
                elif parts[0] == "VECTOR":
                    _, sx, sy, ex, ey, color, name, dx, dy, style = parts
                    self.vectors.append((float(sx), float(sy), float(ex), float(ey),
                                         color, name, float(dx), float(dy), style))

        self.update_start_selector()
        self.update_reference_selector()
        self.update_tree()
        self.redraw_plot()
    # ---------- GUI opdateringer ----------
    def update_tree(self):
        self.tree.delete(*self.tree.get_children())
        self.item_map.clear()

        # Punkter
        for i, (x, y, name) in enumerate(self.points):
            values = ("Punkt", name,
                      f"{x:.3f}", f"{y:.3f}",
                      "", "", "", "", "", "")
            item = self.tree.insert("", "end", values=values)
            self.item_map[item] = ("point", i)

        # Reference-linjer
        for i, r in enumerate(self.references):
            sx, sy, ex, ey, angle, name = r
            dx = ex - sx
            dy = ey - sy
            length = (dx*dx + dy*dy)**0.5
            values = ("Reference", name,
                      f"{sx:.3f}", f"{sy:.3f}",
                      f"{ex:.3f}", f"{ey:.3f}",
                      f"{length:.3f}", f"{angle:.3f}",
                      "gray", "dashed")
            item = self.tree.insert("", "end", values=values)
            self.item_map[item] = ("reference", i)

        # Vektorer
        for i, v in enumerate(self.vectors):
            sx, sy, ex, ey, color, name, dx_label, dy_label, style = v
            dx = ex - sx
            dy = ey - sy
            length = (dx*dx + dy*dy)**0.5
            angle = np.degrees(np.arctan2(dy, dx))
            values = ("Vektor", name,
                      f"{sx:.3f}", f"{sy:.3f}",
                      f"{ex:.3f}", f"{ey:.3f}",
                      f"{length:.3f}", f"{angle:.3f}",
                      color, style)
            item = self.tree.insert("", "end", values=values)
            self.item_map[item] = ("vector", i)
        # Vinkler
        for i, (angle, name, _, _, _) in enumerate(self.angles):
            values = ("Vinkel", name,
                    "", "", "", "",
                    "", f"{angle:.3f}",
                    "", "")
            item = self.tree.insert("", "end", values=values)
            self.item_map[item] = ("angle", i)

    def update_start_selector(self):
        items = ["origin"]

        # Punkter
        for i, (x, y, name) in enumerate(self.points):
            if name.strip() == "":
                items.append(f"point #{i}")
            else:
                items.append(f"point #{i} ({name})")

        # Vektorer
        for i, v in enumerate(self.vectors):
            name = v[5]
            if name.strip() == "":
                items.append(f"vector #{i}")
            else:
                items.append(f"vector #{i} ({name})")

        self.start_selector["values"] = items

        # Bevar gyldig værdi
        current = self.start_mode.get()
        if not any(current.startswith(x.split()[0]) for x in items):
            self.start_mode.set("origin")

    def update_reference_selector(self):
        items = ["Standard"]

        for i, r in enumerate(self.references):
            name = r[5]
            if name.strip() == "":
                items.append(f"reference #{i}")
            else:
                items.append(f"reference #{i} ({name})")

        self.ref_selector["values"] = items

        if self.ref_var.get() not in items:
            self.ref_var.set("Standard")

    # ---------- Vektorsum (ALTID dotted, fra origo) ----------
    def create_vector_sum(self):
        if len(self.last_selected) != 2:
            print("Vælg præcis to vektorer.")
            return

        item1, item2 = self.last_selected

        kind1, i1 = self.item_map[item1]
        kind2, i2 = self.item_map[item2]

        if kind1 != "vector" or kind2 != "vector":
            print("Begge valgte elementer skal være vektorer.")
            return

        sx1, sy1, ex1, ey1, color1, name1, dx1, dy1, style1 = self.vectors[i1]
        sx2, sy2, ex2, ey2, color2, name2, dx2, dy2, style2 = self.vectors[i2]

        v1_dx = ex1 - sx1
        v1_dy = ey1 - sy1
        v2_dx = ex2 - sx2
        v2_dy = ey2 - sy2

        sum_dx = v1_dx + v2_dx 
        sum_dy = v1_dy + v2_dy
        # Hvis de to vektorer har samme startpunkt → brug det # Ellers → brug origo 
        if sx1 == sx2 and sy1 == sy2: 
            sx = sx1 
            sy = sy1 
        else: 
            sx = 0 
            sy = 0 

        ex = sx + sum_dx 
        ey = sy + sum_dy

        color = self.color_var.get()
        style = "dotted"
        name = f"S{len(self.vectors) + 1}"
        dx = 0.2
        dy = 0.2

        self.vectors.append((sx, sy, ex, ey, color, name, dx, dy, style))

        self.update_tree()
        self.update_start_selector()
        self.redraw_plot()

    # ---------- Geometrisk vektorforskel (A - B) ----------
    def create_vector_difference(self):
        # Brug klikrækkefølgen
        if len(self.last_selected) != 2:
            print("Vælg præcis to vektorer.")
            return

        item1, item2 = self.last_selected

        # Tjek at de stadig er markeret
        if item1 not in self.tree.selection() or item2 not in self.tree.selection():
            print("Marker begge vektorer (CTRL-klik).")
            return

        kind1, i1 = self.item_map[item1]
        kind2, i2 = self.item_map[item2]

        if kind1 != "vector" or kind2 != "vector":
            print("Begge valgte elementer skal være vektorer.")
            return



        sx1, sy1, ex1, ey1, color1, name1, dx1, dy1, style1 = self.vectors[i1]
        sx2, sy2, ex2, ey2, color2, name2, dx2, dy2, style2 = self.vectors[i2]

        sx = ex2
        sy = ey2
        ex = ex1
        ey = ey1

        color = self.color_var.get()
        style = "dashed"
        name = f"D{len(self.vectors) + 1}"
        dx = 0.2
        dy = 0.2

        self.vectors.append((sx, sy, ex, ey, color, name, dx, dy, style))

        self.update_tree()
        self.update_start_selector()
        self.redraw_plot()

    # ---------- Resulterende vektor mellem to vektorer ----------
    def create_resultant_vector(self):
        sel = self.tree.selection()
        if len(sel) != 2:
            print("Vælg præcis to vektorer.")
            return

        indices = []
        for s in sel:
            if s not in self.item_map:
                return
            kind, idx = self.item_map[s]
            if kind != "vector":
                print("Begge valgte elementer skal være vektorer.")
                return
            indices.append(idx)

        i1, i2 = indices

        sx1, sy1, ex1, ey1, color1, name1, dx1, dy1, style1 = self.vectors[i1]
        sx2, sy2, ex2, ey2, color2, name2, dx2, dy2, style2 = self.vectors[i2]

        sx = sx1
        sy = sy1
        ex = ex2
        ey = ey2

        color = self.color_var.get()
        style = self.style_var.get()
        name = f"R{len(self.vectors) + 1}"
        dx = 0.2
        dy = 0.2

        self.vectors.append((sx, sy, ex, ey, color, name, dx, dy, style))

        self.update_tree()
        self.update_start_selector()
        self.redraw_plot()
    # ---------- Reference-linje ----------
    def create_reference_line(self):
        mode = self.start_mode.get()

        # Startpunkt
        if mode == "origin":
            sx, sy = 0, 0
        elif mode.startswith("point #"):
            idx = int(mode.split("#")[1].split()[0])
            sx, sy, _ = self.points[idx]
        else:
            sx, sy = 0, 0

        # Reference-vinkel
        ref = self.ref_var.get()

        if ref == "Standard":
            base_angle = 0
        else:
            if "#" in ref:
                idx = int(ref.split("#")[1].split()[0])
                sxr, syr, exr, eyr, ref_angle, rname = self.references[idx]
                base_angle = np.radians(ref_angle)
            else:
                base_angle = 0

        # Brugeren angiver en ekstra vinkel
        added_angle = np.radians(self.angle_var.get())

        # Total vinkel
        total_angle = base_angle + added_angle

        # Fast længde (kan redigeres i Treeview)
        length = 5.0

        dx = length * np.cos(total_angle)
        dy = length * np.sin(total_angle)

        ex = sx + dx
        ey = sy + dy

        # Navn
        name = f"Ref{len(self.references) + 1}"
        angle_deg = np.degrees(total_angle)

        # Gem reference-linje
        self.references.append((sx, sy, ex, ey, angle_deg, name))

        self.update_reference_selector()
        self.update_tree()
        self.redraw_plot()
    # ---------- Vinkel Bue----------
    def create_angle_between(self):
        if len(self.last_selected) != 2:
            print("Vælg præcis to elementer.")
            return

        item1, item2 = self.last_selected

        kind1, i1 = self.item_map[item1]
        kind2, i2 = self.item_map[item2]

        if kind1 not in ("vector", "reference") or kind2 not in ("vector", "reference"):
            print("Vælg to vektorer eller en vektor og en reference.")
            return

        # Hent data
        if kind1 == "vector":
            sx1, sy1, ex1, ey1, *_ = self.vectors[i1]
        else:
            sx1, sy1, ex1, ey1, angle_ref, _ = self.references[i1]

        if kind2 == "vector":
            sx2, sy2, ex2, ey2, *_ = self.vectors[i2]
        else:
            sx2, sy2, ex2, ey2, angle_ref, _ = self.references[i2]

        # Beregn vinkler
        dx1, dy1 = ex1 - sx1, ey1 - sy1
        dx2, dy2 = ex2 - sx2, ey2 - sy2

        a1 = np.arctan2(dy1, dx1)
        a2 = np.arctan2(dy2, dx2)

        angle = np.degrees(a2 - a1)
        angle = (angle + 360) % 360
        if angle > 180:
            angle = 360 - angle

        # Gem i liste
        name = f"θ{len(self.angles)+1}"
        self.angles.append((angle, name, (sx1, sy1), a1, a2))

        self.update_tree()
        self.redraw_plot()

    
    #-----Undersænket funtkion------
    def format_label(self, name):
        if "_" in name:
            parts = name.split("_", 1)
            return f"{parts[0]}$_{{{parts[1]}}}$"
        return name


    # ---------- Tegn alt ----------
    def redraw_plot(self):
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        self.ax.clear()
        self.ax.grid(True)
        self.ax.set_aspect("equal", adjustable="box")

        self.text_objects = []
        self.point_objects = []

        # Punkter
        if self.show_points.get():
            for x, y, name in self.points:
                p = self.ax.scatter(x, y, s=POINT_SIZE, color="black", picker=True)
                self.point_objects.append(p)
                self.ax.text(x + 0.1, y + 0.1, name, fontsize=9, color="black")

        # Reference-linjer
        for sx, sy, ex, ey, angle, name in self.references:
            arrow = FancyArrowPatch(
                (sx, sy), (ex, ey),
                arrowstyle='-',
                color="gray",
                linestyle="dashed",
                mutation_scale=10
            )
            self.ax.add_patch(arrow)

            # Navn på reference-linje
            if self.show_names.get() and name.strip():
                mx = (sx + ex) / 2
                my = (sy + ey) / 2
                self.ax.text(mx, my, name, fontsize=9, color="gray")

        # Vektorer
        for sx, sy, ex, ey, color, name, dx, dy, style in self.vectors:
            arrow = FancyArrowPatch(
                (sx, sy), (ex, ey),
                arrowstyle='->',
                color=color,
                linestyle=style,
                mutation_scale=15
            )
            self.ax.add_patch(arrow)

            if self.show_names.get() and name:
                txt = self.ax.text(ex + dx, ey + dy, self.format_label(name),
                   fontsize=10, color=color, picker=True)
                self.text_objects.append(txt)

        self.ax.set_xlim(xlim)
        self.ax.set_ylim(ylim)
        # Tegn vinkel-buer
        for angle, name, center, a1, a2 in self.angles:
            cx, cy = center
            arc = Arc((cx, cy),
                        2, 2,
                        angle=0,
                        theta1=np.degrees(a1),
                        theta2=np.degrees(a2),
                        color="purple")
            self.ax.add_patch(arc)
            self.ax.text(cx + 1.2, cy + 1.2, f"{angle:.1f}°", color="purple")

        self.canvas.draw()

    # ---------- Ryd ----------
    def clear_plot(self):
        self.vectors = []
        self.points = []
        self.references = []
        self.update_tree()
        self.update_start_selector()
        self.update_reference_selector()
        self.redraw_plot()

    # ---------- Zoom ----------
    def apply_zoom(self):
        # Global scaling af hele Tkinter-GUI'en
        root = self.frame.winfo_toplevel()
        root.tk.call('tk', 'scaling', self.ui_scale)

        # Opdater alle standard fonts
        default_font = tk.font.nametofont("TkDefaultFont")
        text_font = tk.font.nametofont("TkTextFont")
        fixed_font = tk.font.nametofont("TkFixedFont")

        default_font.configure(size=int(10 * self.ui_scale))
        text_font.configure(size=int(10 * self.ui_scale))
        fixed_font.configure(size=int(10 * self.ui_scale))
        # Skaler Treeview-rækkehøjde 
        style = ttk.Style() 
        style.configure("Treeview", rowheight=int(20 * self.ui_scale))

        # Opdater label
        self.zoom_label.config(text=f"{int(self.ui_scale * 100)}%")

        # Tving redraw af UI
        self.frame.update_idletasks()

        # ---------- NY DEL: Zoom på matplotlib-aksen ----------
        scale = self.ui_scale

        # Find center af nuværende view
        x_center = (self.ax.get_xlim()[0] + self.ax.get_xlim()[1]) / 2
        y_center = (self.ax.get_ylim()[0] + self.ax.get_ylim()[1]) / 2

        # Standard-range (samme som din start)
        base_x_range = 40
        base_y_range = 20

        # Beregn ny range baseret på zoom
        new_x_range = base_x_range / scale
        new_y_range = base_y_range / scale

        # Sæt nye limits
        self.ax.set_xlim(x_center - new_x_range/2, x_center + new_x_range/2)
        self.ax.set_ylim(y_center - new_y_range/2, y_center + new_y_range/2)

        # Redraw plot
        self.canvas.draw()
        # ---------- NY DEL: Skaler canvas-størrelsen ----------
        new_width = int(800 * self.ui_scale)
        new_height = int(400 * self.ui_scale)

        self.canvas.get_tk_widget().config(width=new_width, height=new_height)
        self.fig.set_size_inches(new_width / 100, new_height / 100)



    def zoom_in(self):
        if self.ui_scale < 2.0:
            self.ui_scale += 0.1
            self.apply_zoom()

    def zoom_out(self):
        if self.ui_scale > 0.7:
            self.ui_scale -= 0.1
            self.apply_zoom()




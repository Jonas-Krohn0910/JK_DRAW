import os
import tkinter as tk
from tkinter import ttk, filedialog
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.patches import FancyArrowPatch, Arc

GRID_STEP = 0.2
POINT_SIZE = 10


def pol2cart_horizontal(length, angle_deg):
    angle_rad = np.radians(angle_deg)
    return length * np.cos(angle_rad), length * np.sin(angle_rad)


def pol2cart_vertical(length, angle_deg):
    angle_rad = np.radians(angle_deg)
    return length * np.sin(angle_rad), length * np.cos(angle_rad)


class OffsetDialog(tk.Toplevel):
    def __init__(self, parent, sx, sy):
        super().__init__(parent)
        self.title("Offset vektor")
        self.resizable(False, False)

        self.result = None

        tk.Label(self, text="Ny X1:").grid(row=0, column=0, padx=10, pady=5)
        self.x_entry = tk.Entry(self)
        self.x_entry.grid(row=0, column=1, padx=10, pady=5)
        self.x_entry.insert(0, f"{sx}")

        tk.Label(self, text="Ny Y1:").grid(row=1, column=0, padx=10, pady=5)
        self.y_entry = tk.Entry(self)
        self.y_entry.grid(row=1, column=1, padx=10, pady=5)
        self.y_entry.insert(0, f"{sy}")

        ok_btn = tk.Button(self, text="OK", command=self.on_ok)
        ok_btn.grid(row=2, column=0, columnspan=2, pady=10)

        btn_start = tk.Button(self, text="Brug startpunkt fra vektor", command=self.use_vector_start)
        btn_start.grid(row=3, column=0, columnspan=2, pady=5)

        btn_end = tk.Button(self, text="Brug slutpunkt fra vektor", command=self.use_vector_end)
        btn_end.grid(row=4, column=0, columnspan=2, pady=5)

        self.x_entry.focus_set()
        self.grab_set()
        self.wait_window()

    def on_ok(self):
        try:
            new_x = float(self.x_entry.get().replace(",", "."))
            new_y = float(self.y_entry.get().replace(",", "."))
            self.result = (new_x, new_y)
        except ValueError:
            self.result = None
        self.destroy()

    def use_vector_start(self):
        self.result = "USE_VECTOR_START"
        self.destroy()

    def use_vector_end(self):
        self.result = "USE_VECTOR_END"
        self.destroy()


class ScaleDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Skalér vektor")
        self.resizable(False, False)

        self.result = None

        tk.Label(self, text="Skaleringsfaktor:").grid(row=0, column=0, padx=10, pady=5)
        self.entry = tk.Entry(self)
        self.entry.grid(row=0, column=1, padx=10, pady=5)
        self.entry.insert(0, "1.0")

        ok_btn = tk.Button(self, text="OK", command=self.on_ok)
        ok_btn.grid(row=1, column=0, columnspan=2, pady=10)

        self.entry.focus_set()
        self.grab_set()
        self.wait_window()

    def on_ok(self):
        try:
            factor = float(self.entry.get().replace(",", "."))
            self.result = factor
        except ValueError:
            self.result = None
        self.destroy()


class VectorPickDialog(tk.Toplevel):
    def __init__(self, parent, vectors):
        super().__init__(parent)
        self.title("Vælg vektor")
        self.resizable(False, False)

        self.result = None  # (index, display_name)

        tk.Label(self, text="Vælg en vektor:").pack(padx=10, pady=(10, 5))

        self.listbox = tk.Listbox(self, width=40, height=10)
        self.listbox.pack(padx=10, pady=5)

        for i, v in enumerate(vectors):
            sx, sy, ex, ey, color, name, dx, dy, style = v
            display_name = name.strip() if name.strip() else f"Vektor #{i}"
            self.listbox.insert(tk.END, f"{i}: {display_name}")

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="OK", width=8, command=self.on_ok).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Annuller", width=8, command=self.on_cancel).grid(row=0, column=1, padx=5)

        self.listbox.bind("<Double-Button-1>", lambda e: self.on_ok())

        self.grab_set()
        self.listbox.focus_set()

    def on_ok(self):
        sel = self.listbox.curselection()
        if not sel:
            self.result = None
        else:
            idx = sel[0]
            text = self.listbox.get(idx)
            display_name = text.split(":", 1)[1].strip()
            self.result = (idx, display_name)
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()


class VectorOperationDialog(tk.Toplevel):
    def __init__(self, parent, images, vectors):
        super().__init__(parent)
        self.title("Vektoroperationer")
        self.resizable(True, True)

        self.images = images
        self.vectors = vectors
        self.result = None
        self.v1_idx = None
        self.v2_idx = None

        self.operation_var = tk.StringVar(value="Vektorsum")
        tk.Label(self, text="Operation:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.op_combo = ttk.Combobox(
            self,
            textvariable=self.operation_var,
            values=["Vektorsum", "Vektorforskel", "Resultant", "Vinkel mellem"],
            state="readonly",
            width=20
        )
        self.op_combo.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.op_combo.bind("<<ComboboxSelected>>", self.on_operation_change)

        self.image_label = tk.Label(self)
        self.image_label.grid(row=1, column=0, columnspan=2, padx=10, pady=10)
        self.update_image()

        tk.Label(self, text="Vektor 1:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        v1_frame = tk.Frame(self)
        v1_frame.grid(row=2, column=1, padx=10, pady=5, sticky="we")
        v1_frame.columnconfigure(0, weight=1)

        self.v1_var = tk.StringVar(value="")
        self.v1_entry = tk.Entry(v1_frame, textvariable=self.v1_var)
        self.v1_entry.grid(row=0, column=0, sticky="we")
        self.v1_entry.bind("<Key>", lambda e: "break")
        self.v1_entry.bind("<Button-1>", lambda e: self.pick_vector("v1"))

        tk.Button(
            v1_frame,
            text="+",
            width=2,
            command=lambda: self.pick_vector("v1")
        ).grid(row=0, column=1, padx=(5, 0))

        tk.Label(self, text="Vektor 2:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
        v2_frame = tk.Frame(self)
        v2_frame.grid(row=3, column=1, padx=10, pady=5, sticky="we")
        v2_frame.columnconfigure(0, weight=1)

        self.v2_var = tk.StringVar(value="")
        self.v2_entry = tk.Entry(v2_frame, textvariable=self.v2_var)
        self.v2_entry.grid(row=0, column=0, sticky="we")
        self.v2_entry.bind("<Key>", lambda e: "break")
        self.v2_entry.bind("<Button-1>", lambda e: self.pick_vector("v2"))

        tk.Button(
            v2_frame,
            text="+",
            width=2,
            command=lambda: self.pick_vector("v2")
        ).grid(row=0, column=1, padx=(5, 0))

        btn_frame = tk.Frame(self)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        tk.Button(btn_frame, text="OK", width=10, command=self.on_ok).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Annuller", width=10, command=self.on_cancel).grid(row=0, column=1, padx=5)

        self.columnconfigure(1, weight=1)
        self.after(10, lambda: self.grab_set())

    def on_operation_change(self, event=None):
        self.update_image()

    def update_image(self):
        op = self.operation_var.get()
        img = self.images.get(op)
        if img is not None:
            self.image_label.configure(image=img)
            self.image_label.image = img
        else:
            self.image_label.configure(image="", text=op)

    def pick_vector(self, which):
        if not self.vectors:
            return
        picker = VectorPickDialog(self, self.vectors)
        self.wait_window(picker)
        if picker.result is None:
            return
        idx, display_name = picker.result
        if which == "v1":
            self.v1_idx = idx
            self.v1_var.set(display_name)
        else:
            self.v2_idx = idx
            self.v2_var.set(display_name)

    def on_ok(self):
        op = self.operation_var.get()
        if self.v1_idx is None or self.v2_idx is None:
            self.destroy()
            return
        self.result = (op, self.v1_idx, self.v2_idx)
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()
class VectorTab:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)

        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)

        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.ax.set_aspect("equal", adjustable="box")
        self.ax.grid(True)
        self.ax.set_xlim(-10, 30)
        self.ax.set_ylim(-10, 10)

        self.canvas_container = ttk.Frame(self.frame)
        self.canvas_container.grid(row=0, column=0, columnspan=3, sticky="nsew")

        self.canvas_container.rowconfigure(0, weight=1)
        self.canvas_container.columnconfigure(0, weight=1)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_container)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side="left", fill="both", expand=True)

        self.resize_handle = tk.Label(
            self.canvas_container,
            text="⧉",
            cursor="bottom_right_corner"
        )
        self.resize_handle.place(relx=1.0, rely=1.0, anchor="se")

        self.resize_handle.bind("<ButtonPress-1>", self.start_resize)
        self.resize_handle.bind("<B1-Motion>", self.perform_resize)

        self.toolbar_frame = ttk.Frame(self.frame)
        self.toolbar_frame.grid(row=1, column=0, columnspan=3, sticky="w")
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        self.toolbar.update()

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

        self.show_grid = tk.BooleanVar(value=True)
        ttk.Checkbutton(file_frame, text="Vis grid", variable=self.show_grid,
                        command=self.redraw_plot).grid(row=5, column=0, pady=5)

        list_frame = ttk.LabelFrame(self.frame, text="Punkter og vektorer")
        list_frame.grid(row=2, column=2, padx=10, pady=10, sticky="n")
        list_frame.columnconfigure(0, weight=0)
        list_frame.columnconfigure(1, weight=0)

        columns = ("type", "name", "x1", "y1", "x2", "y2", "length", "angle", "color", "style")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=18)
        self.tree.grid(row=0, column=0, padx=5, pady=5)

        self.tree_menu = tk.Menu(self.tree, tearoff=0)
        self.tree_menu.add_command(label="Offset…", command=self.offset_selected_vector)
        self.tree_menu.add_command(label="Skalér…", command=self.scale_selected_vector)
        self.tree_menu.add_command(label="Vektoroperationer…", command=self.open_vector_operations_dialog)
        self.tree_menu.add_command(label="Slet", command=self.remove_selected_item)

        self.tree.bind("<Button-3>", self.on_tree_right_click)

        headers = ["Type", "Navn", "X1", "Y1", "X2", "Y2", "Længde", "Vinkel (°)", "Farve", "Linje"]
        for col, text in zip(columns, headers):
            self.tree.heading(col, text=text)

        for col, w in zip(columns, (70, 80, 60, 60, 60, 60, 70, 70, 70, 70)):
            self.tree.column(col, width=w, anchor="center")

        button_frame = ttk.Frame(list_frame)
        button_frame.grid(row=1, column=0, pady=10)

        ttk.Button(
            button_frame,
            text="Vektoroperationer…",
            command=self.open_vector_operations_dialog
        ).grid(row=0, column=0, padx=5, pady=5)

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
        self.pending_offset = None

        self.fig.canvas.mpl_connect("pick_event", self.on_pick)
        self.fig.canvas.mpl_connect("motion_notify_event", self.on_drag)
        self.fig.canvas.mpl_connect("button_release_event", self.on_release)
        self.fig.canvas.mpl_connect("button_press_event", self.on_click)

        self.tree.bind("<Double-1>", self.on_tree_double_click)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        picture_dir = os.path.join(base_dir, "pictures")
        self.operation_images = {}
        try:
            self.operation_images["Vektorsum"] = tk.PhotoImage(file=os.path.join(picture_dir, "sum.png"))
        except Exception:
            self.operation_images["Vektorsum"] = None
        try:
            self.operation_images["Vektorforskel"] = tk.PhotoImage(file=os.path.join(picture_dir, "difference.png"))
        except Exception:
            self.operation_images["Vektorforskel"] = None
        try:
            self.operation_images["Resultant"] = tk.PhotoImage(file=os.path.join(picture_dir, "resultant.png"))
        except Exception:
            self.operation_images["Resultant"] = None
        try:
            self.operation_images["Vinkel mellem"] = tk.PhotoImage(file=os.path.join(picture_dir, "angle.png"))
        except Exception:
            self.operation_images["Vinkel mellem"] = None
    #----Resize----
    def start_resize(self, event):
        widget = self.canvas_widget
        self.resize_start = (
            event.x_root,
            event.y_root,
            widget.winfo_width(),
            widget.winfo_height()
        )

    def perform_resize(self, event):
        start_x, start_y, start_w, start_h = self.resize_start

        dx = event.x_root - start_x
        dy = event.y_root - start_y

        new_w = max(300, start_w + dx)
        new_h = max(200, start_h + dy)

        self.canvas_widget.config(width=new_w, height=new_h)

        dpi = self.fig.get_dpi()
        self.fig.set_size_inches(new_w / dpi, new_h / dpi, forward=True)

        self.canvas.draw_idle()

    #-------Skalering af vektorer---------
    def scale_selected_vector(self):
        sel = self.tree.selection()
        if not sel:
            return

        item = sel[0]
        if item not in self.item_map:
            return

        kind, idx = self.item_map[item]
        if kind != "vector":
            return

        sx, sy, ex, ey, color, name, dx, dy, style = self.vectors[idx]

        vx = ex - sx
        vy = ey - sy

        dialog = ScaleDialog(self.frame)
        if dialog.result is None:
            return

        factor = dialog.result

        new_ex = sx + vx * factor
        new_ey = sy + vy * factor

        self.vectors[idx] = (
            sx, sy,
            new_ex, new_ey,
            color, name,
            dx, dy,
            style
        )

        self.update_tree()
        self.redraw_plot()

    def on_tree_right_click(self, event):
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return

        self.tree.selection_set(row_id)
        self.tree_menu.tk_popup(event.x_root, event.y_root)

    def offset_selected_vector(self):
        sel = self.tree.selection()
        if not sel:
            return

        item = sel[0]
        if item not in self.item_map:
            return

        kind, idx = self.item_map[item]
        if kind != "vector":
            return

        sx, sy, ex, ey, color, name, dx, dy, style = self.vectors[idx]

        dialog = OffsetDialog(self.frame, sx, sy)
        if dialog.result is None:
            return

        if dialog.result == "USE_VECTOR_START":
            self.pending_offset = ("start", idx)
            self.tree.bind("<ButtonRelease-1>", self.finish_offset_with_vector)
            return

        if dialog.result == "USE_VECTOR_END":
            self.pending_offset = ("end", idx)
            self.tree.bind("<ButtonRelease-1>", self.finish_offset_with_vector)
            return

        new_x, new_y = dialog.result

        delta_x = new_x - sx
        delta_y = new_y - sy

        self.vectors[idx] = (
            new_x,
            new_y,
            ex + delta_x,
            ey + delta_y,
            color,
            name,
            dx,
            dy,
            style
        )

        self.update_tree()
        self.redraw_plot()

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

        if self.dragging_point is not None and self.dragging_point < len(self.points):
            x, y, name = self.points[self.dragging_point]
            new_x = round(event.xdata / GRID_STEP) * GRID_STEP
            new_y = round(event.ydata / GRID_STEP) * GRID_STEP
            self.points[self.dragging_point] = (new_x, new_y, name)

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

    def on_tree_double_click(self, event):
        if self.edit_state is not None:
            return

        item = self.tree.identify_row(event.y)
        if not item or item not in self.item_map:
            return

        kind, idx = self.item_map[item]

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

        if kind == "vector":
            sx, sy, ex, ey, color, name, dx, dy, style = self.vectors[idx]

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

        rad = np.radians(angle)
        ex = sx + new_length * np.cos(rad)
        ey = sy + new_length * np.sin(rad)

        self.references[idx] = (sx, sy, ex, ey, angle, name)

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

    def load_project(self):
        path = filedialog.askopenfilename()
        if not path:
            return

        self.points = []
        self.vectors = []
        self.references = []

        with open(path, "r") as f:
            for line in f:
                parts = line.strip().split()

                if parts[0] == "POINT":
                    _, x, y, name = parts
                    self.points.append((float(x), float(y), name))

                elif parts[0] == "VECTOR":
                    if len(parts) != 10:
                        print("Ugyldig VECTOR-linje:", parts)
                        continue

                    _, sx, sy, ex, ey, color, name, dx, dy, style = parts

                    self.vectors.append((
                        float(sx), float(sy),
                        float(ex), float(ey),
                        color, name,
                        float(dx), float(dy),
                        style
                    ))

        self.update_start_selector()
        self.update_reference_selector()
        self.update_tree()
        self.redraw_plot()

    # ---------- GUI opdateringer ----------
    def update_tree(self):
        self.tree.delete(*self.tree.get_children())
        self.item_map.clear()

        for i, (x, y, name) in enumerate(self.points):
            values = ("Punkt", name,
                      f"{x:.3f}", f"{y:.3f}",
                      "", "", "", "", "", "")
            item = self.tree.insert("", "end", values=values)
            self.item_map[item] = ("point", i)

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

        for i, (angle, name, _, _, _) in enumerate(self.angles):
            values = ("Vinkel", name,
                      "", "", "", "",
                      "", f"{angle:.3f}",
                      "", "")
            item = self.tree.insert("", "end", values=values)
            self.item_map[item] = ("angle", i)

    def update_start_selector(self):
        items = ["origin"]

        for i, (x, y, name) in enumerate(self.points):
            if name.strip() == "":
                items.append(f"point #{i}")
            else:
                items.append(f"point #{i} ({name})")

        for i, v in enumerate(self.vectors):
            name = v[5]
            if name.strip() == "":
                items.append(f"vector #{i}")
            else:
                items.append(f"vector #{i} ({name})")

        self.start_selector["values"] = items

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

    # ---------- Vektoroperationer ----------
    def open_vector_operations_dialog(self):
        if not self.vectors:
            return
        dialog = VectorOperationDialog(self.frame, self.operation_images, self.vectors)
        self.frame.wait_window(dialog)
        if dialog.result is None:
            return
        op, i1, i2 = dialog.result
        self.perform_vector_operation(op, i1, i2)

    def perform_vector_operation(self, op, i1, i2):
        if op == "Vektorsum":
            self._op_vector_sum(i1, i2)
        elif op == "Vektorforskel":
            self._op_vector_difference(i1, i2)
        elif op == "Resultant":
            self._op_resultant(i1, i2)
        elif op == "Vinkel mellem":
            self._op_angle_between(i1, i2)

    def _op_vector_sum(self, i1, i2):
        sx1, sy1, ex1, ey1, color1, name1, dx1, dy1, style1 = self.vectors[i1]
        sx2, sy2, ex2, ey2, color2, name2, dx2, dy2, style2 = self.vectors[i2]

        v1_dx = ex1 - sx1
        v1_dy = ey1 - sy1
        v2_dx = ex2 - sx2
        v2_dy = ey2 - sy2

        sum_dx = v1_dx + v2_dx
        sum_dy = v1_dy + v2_dy

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

    def _op_vector_difference(self, i1, i2):
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

    def _op_resultant(self, i1, i2):
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

    def _op_angle_between(self, i1, i2):
        sx1, sy1, ex1, ey1, *_ = self.vectors[i1]
        sx2, sy2, ex2, ey2, *_ = self.vectors[i2]

        dx1, dy1 = ex1 - sx1, ey1 - sy1
        dx2, dy2 = ex2 - sx2, ey2 - sy2

        a1 = np.arctan2(dy1, dx1)
        a2 = np.arctan2(dy2, dx2)

        angle = np.degrees(a2 - a1)
        angle = (angle + 360) % 360
        if angle > 180:
            angle = 360 - angle

        name = f"θ{len(self.angles)+1}"
        self.angles.append((angle, name, (sx1, sy1), a1, a2))

        self.update_tree()
        self.redraw_plot()
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
        self.ax.grid(self.show_grid.get())
        self.ax.set_aspect("equal", adjustable="box")

        self.text_objects = []
        self.point_objects = []

        if self.show_points.get():
            for x, y, name in self.points:
                p = self.ax.scatter(x, y, s=POINT_SIZE, color="black", picker=True)
                self.point_objects.append(p)
                self.ax.text(x + 0.1, y + 0.1, name, fontsize=9, color="black")

        for sx, sy, ex, ey, angle, name in self.references:
            arrow = FancyArrowPatch(
                (sx, sy), (ex, ey),
                arrowstyle='-',
                color="gray",
                linestyle="dashed",
                mutation_scale=10
            )
            self.ax.add_patch(arrow)

            if self.show_names.get() and name.strip():
                mx = (sx + ex) / 2
                my = (sy + ey) / 2
                self.ax.text(mx, my, name, fontsize=9, color="gray")

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
                mx = (sx + ex) / 2
                my = (sy + ey) / 2

                txt = self.ax.text(
                    mx + dx, my + dy,
                    self.format_label(name),
                    fontsize=10,
                    color=color,
                    picker=True
                )
                self.text_objects.append(txt)

        self.ax.set_xlim(xlim)
        self.ax.set_ylim(ylim)

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

    def finish_offset_with_vector(self, event):
        row = self.tree.identify_row(event.y)
        if not row or row not in self.item_map:
            return

        kind, idx2 = self.item_map[row]
        if kind != "vector":
            return

        mode, idx1 = self.pending_offset

        sx1, sy1, ex1, ey1, color, name, dx, dy, style = self.vectors[idx1]
        sx2, sy2, ex2, ey2, *_ = self.vectors[idx2]

        if mode == "start":
            ref_x, ref_y = sx2, sy2
        else:
            ref_x, ref_y = ex2, ey2

        delta_x = ref_x - sx1
        delta_y = ref_y - sy1

        self.vectors[idx1] = (
            ref_x, ref_y,
            ex1 + delta_x, ey1 + delta_y,
            color, name, dx, dy, style
        )

        self.pending_offset = None
        self.tree.unbind("<ButtonRelease-1>")

        self.update_tree()
        self.redraw_plot()

    # ---------- Reference-linje ----------
    def create_reference_line(self):
        mode = self.start_mode.get()

        if mode == "origin":
            sx, sy = 0, 0
        elif mode.startswith("point #"):
            idx = int(mode.split("#")[1].split()[0])
            sx, sy, _ = self.points[idx]
        else:
            sx, sy = 0, 0

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

        added_angle = np.radians(self.angle_var.get())
        total_angle = base_angle + added_angle

        length = 5.0

        dx = length * np.cos(total_angle)
        dy = length * np.sin(total_angle)

        ex = sx + dx
        ey = sy + dy

        name = f"Ref{len(self.references) + 1}"
        angle_deg = np.degrees(total_angle)

        self.references.append((sx, sy, ex, ey, angle_deg, name))

        self.update_reference_selector()
        self.update_tree()
        self.redraw_plot()

    # ---------- Ryd ----------
    def clear_plot(self):
        self.vectors = []
        self.points = []
        self.references = []
        self.angles = []
        self.update_tree()
        self.update_start_selector()
        self.update_reference_selector()
        self.redraw_plot()

    def get_frame(self):
        return self.frame

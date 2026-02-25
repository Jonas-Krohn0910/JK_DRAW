import math
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog

from ac_solver import ACSolver

GRID = 20


# ---------------------------------------------------------
# PORT
# ---------------------------------------------------------
class Port:
    def __init__(self, canvas, component, dx, dy):
        self.canvas = canvas
        self.component = component
        self.dx = dx
        self.dy = dy
        self.x = component.x + dx
        self.y = component.y + dy
        self.node_id = None

        self.id = canvas.create_oval(
            self.x - 3, self.y - 3,
            self.x + 3, self.y + 3,
            fill="black"
        )
        canvas.itemconfigure(self.id, state="hidden")

    def update(self):
        self.x = self.component.x + self.dx
        self.y = self.component.y + self.dy
        self.canvas.coords(
            self.id,
            self.x - 3, self.y - 3,
            self.x + 3, self.y + 3
        )


class Wire:
    HANDLE_RADIUS = 8

    def __init__(self, canvas, port_a, port_b, style=1):
        self.canvas = canvas
        self.editor = canvas.editor
        self.port_a = port_a
        self.port_b = port_b
        self.style = style  # 1 = 1 knæk, 2 = 2 knæk

        self.points = []     # [(x,y), ...]
        self.segments = []   # line IDs
        self.handles = []    # handle IDs

        self.dragging_index = None

        self.create_initial_points()
        self.draw()

        port_a.wires = getattr(port_a, "wires", [])
        port_b.wires = getattr(port_b, "wires", [])
        port_a.wires.append(self)
        port_b.wires.append(self)

    def create_initial_points(self):
        x1, y1 = self.port_a.x, self.port_a.y
        x2, y2 = self.port_b.x, self.port_b.y

        if self.style == 1:
            mid_x = (x1 + x2) // 2
            self.points = [
                (x1, y1),
                (mid_x, y1),
                (x2, y2)
            ]
        elif self.style == 2:
            mid_x = (x1 + x2) // 2
            self.points = [
                (x1, y1),
                (mid_x, y1),
                (mid_x, y2),
                (x2, y2)
            ]

    def reset_layout(self):
        self.create_initial_points()
        self.draw()

    def draw(self):
        self.delete_graphics()

        # segmenter
        for i in range(len(self.points) - 1):
            x1, y1 = self.points[i]
            x2, y2 = self.points[i + 1]
            seg = self.canvas.create_line(x1, y1, x2, y2, width=2)
            self.canvas.tag_bind(seg, "<Button-3>", self.on_right_click)
            self.segments.append(seg)

        # handles (kun knæk)
        for i in range(1, len(self.points) - 1):
            x, y = self.points[i]
            h = self.canvas.create_oval(
                x - self.HANDLE_RADIUS, y - self.HANDLE_RADIUS,
                x + self.HANDLE_RADIUS, y + self.HANDLE_RADIUS,
                fill="blue"
            )

            def make_press(index):
                def handler(event):
                    return self.on_handle_press(event, index)
                return handler

            def make_drag(index):
                def handler(event):
                    return self.on_handle_drag(event, index)
                return handler

            self.canvas.tag_bind(h, "<Button-1>", make_press(i))
            self.canvas.tag_bind(h, "<B1-Motion>", make_drag(i))
            self.canvas.tag_bind(h, "<Button-3>", self.on_right_click)
            self.canvas.tag_bind(h, "<ButtonRelease-1>", self.on_handle_release)

            # skjul hvis handles er slået fra
            if not self.editor.show_handles:
                self.canvas.itemconfigure(h, state="hidden")

            self.handles.append(h)


    def on_handle_press(self, event, index):
        self.dragging_index = index
        self.editor.selected_wire = self
        return "break"

    def on_handle_drag(self, event, index):
        if self.dragging_index != index:
            return "break"

        gx = round(event.x / GRID) * GRID
        gy = round(event.y / GRID) * GRID

        # opdater punktet
        self.points[index] = (gx, gy)

        # opdater handle-ovalen (handles[0] svarer til points[1])
        h = self.handles[index - 1]
        self.canvas.coords(
            h,
            gx - self.HANDLE_RADIUS, gy - self.HANDLE_RADIUS,
            gx + self.HANDLE_RADIUS, gy + self.HANDLE_RADIUS
        )

        # opdater de to tilstødende segmenter
        # segment før knækket
        x_prev, y_prev = self.points[index - 1]
        self.canvas.coords(
            self.segments[index - 1],
            x_prev, y_prev, gx, gy
        )

        # segment efter knækket
        x_next, y_next = self.points[index + 1]
        self.canvas.coords(
            self.segments[index],
            gx, gy, x_next, y_next
        )

        return "break"

    def on_handle_release(self, event):
        self.dragging_index = None
        return "break"

    def update(self):
        self.points[0] = (self.port_a.x, self.port_a.y)
        self.points[-1] = (self.port_b.x, self.port_b.y)
        self.draw()

    def on_right_click(self, event):
        self.editor.selected_wire = self
        self.editor.wire_menu.tk_popup(event.x_root, event.y_root)

    def delete_graphics(self):
        for s in self.segments:
            self.canvas.delete(s)
        for h in self.handles:
            self.canvas.delete(h)
        self.segments = []
        self.handles = []

    def delete(self):
        if hasattr(self.port_a, "wires") and self in self.port_a.wires:
            self.port_a.wires.remove(self)
        if hasattr(self.port_b, "wires") and self in self.port_b.wires:
            self.port_b.wires.remove(self)

        if self in self.editor.wires:
            self.editor.wires.remove(self)

        self.delete_graphics()

# ---------------------------------------------------------
# COMPONENT
# ---------------------------------------------------------
class Component:
    def __init__(self, canvas, editor, ctype, x, y, is_source=False):
        self.canvas = canvas
        self.editor = editor
        self.ctype = ctype
        self.is_source = is_source

        if is_source:
            self.x = round(x / GRID) * GRID - 30
            self.y = round(y / GRID) * GRID - 30
        else:
            self.x = round(x / GRID) * GRID
            self.y = round(y / GRID) * GRID


        self.items = []
        self.text_items = []
        self.height = 40
        self.name = self.editor.get_next_name(ctype)

        # Standardværdier
        if ctype == "R":
            self.value_raw = 0.0
            self.value_si = 0.0
        elif ctype == "L":
            self.value_raw = 0.0
            self.value_si = 0.0
        elif ctype == "C":
            self.value_raw = 0.0
            self.value_si = 0.0
        elif ctype == "AC":
            self.voltage_raw = 0.0
            self.frequency_raw = 0.0
            self.voltage_si = 0.0
            self.frequency_si = 0.0

        # -------------------------------------------------
        # Tegn komponent
        # -------------------------------------------------
        if ctype == "GND":
            # Cirkelformet GND-symbol med tre vandrette streger
            radius = 20
            cx = self.x + radius
            cy = self.y + radius

            # Cirkel
            circle = canvas.create_oval(
                cx - radius, cy - radius,
                cx + radius, cy + radius,
                width=2
            )

            # Lodret streg i midten
            vline = canvas.create_line(
                cx, cy - 25,
                cx, cy + 5,
                width=2
            )
            #Vandrette streger 1
            h1 = canvas.create_line(cx - 12, cy + 5,  cx + 12, cy + 5,  width=2)
            #Vandrette streger 2
            h2 = canvas.create_line(cx - 9,  cy + 10, cx + 9,  cy + 10, width=2)     
            #Vandrette streger 3
            h3 = canvas.create_line(cx - 6,  cy + 15, cx + 6,  cy + 15, width=2)

            self.items.extend([circle, vline, h1, h2, h3])
            self.name_text_id = None
            self.value_text_id = None

        elif is_source:
            # AC-kilde: cirkel
            self.id = canvas.create_oval(
                self.x, self.y,
                self.x + 60, self.y + 60,
                fill="white"
            )
            self.height = 60
            self.items.append(self.id)

        elif ctype == "C":
            self.height = 40
            x1, y1 = self.x, self.y
            x2, y2 = self.x + 60, self.y + 40

            self.id = canvas.create_rectangle(
                x1 - 10, y1 - 10,
                x2 + 10, y2 + 10,
                outline=""
            )

            w1 = canvas.create_line(x1, y1 + 20, x1 + 15, y1 + 20, width=3)
            p1 = canvas.create_line(x1 + 20, y1, x1 + 20, y2, width=3)
            p2 = canvas.create_line(x1 + 40, y1, x1 + 40, y2, width=3)
            w2 = canvas.create_line(x1 + 45, y1 + 20, x1 + 60, y1 + 20, width=3)

            self.items.extend([self.id, w1, p1, p2, w2])

        elif ctype == "L":
            self.height = 40
            x1, y1 = self.x, self.y
            y_mid = y1 + 20

            self.id = canvas.create_rectangle(
                x1 - 15, y1 - 15,
                x1 + 75, y1 + 55,
                outline=""
            )

            arcs = []
            for i in range(4):
                arcs.append(canvas.create_arc(
                    x1 + 10 + i * 10, y_mid - 10,
                    x1 + 30 + i * 10, y_mid + 10,
                    start=180, extent=180,
                    style="arc", width=3
                ))

            w1 = canvas.create_line(x1, y_mid, x1 + 10, y_mid, width=3)
            w2 = canvas.create_line(x1 + 50, y_mid, x1 + 60, y_mid, width=3)

            self.items = [self.id] + arcs + [w1, w2]

        else:
            self.id = canvas.create_rectangle(
                self.x, self.y,
                self.x + 60, self.y + 40,
                fill="white"
            )
            self.items.append(self.id)

        # -------------------------------------------------
        # Tekst (ikke for GND)
        # -------------------------------------------------
        if ctype != "GND":
            self.name_text_id = canvas.create_text(
                self.x + 30, self.y + self.height + 0,
                text=self.name, font=("Arial", 9)
            )
            self.value_text_id = canvas.create_text(
                self.x + 30, self.y + self.height + 12,
                text=self.get_value_label(), font=("Arial", 9)
            )
            self.text_items.extend([self.name_text_id, self.value_text_id])

        # -------------------------------------------------
        # Porte
        # -------------------------------------------------
        if ctype == "GND":
            self.ports = [Port(canvas, self, 20, 0)]

        elif ctype == "AC":
            # AC-kilde: KUN 2 porte (top og bund)
            self.ports = [
                Port(canvas, self, 30, 0),             # top
                Port(canvas, self, 30, self.height)    # bund
            ]

        else:
            # R/L/C: 4 porte (venstre, højre, top, bund)
            self.ports = [
                Port(canvas, self, 0, self.height / 2),
                Port(canvas, self, 60, self.height / 2),
                Port(canvas, self, 30, 0),
                Port(canvas, self, 30, self.height)
            ]

        # Bind events
        for item in self.items + self.text_items:
            canvas.tag_bind(item, "<Button-1>", self.on_click)
            canvas.tag_bind(item, "<B1-Motion>", self.on_drag)
            canvas.tag_bind(item, "<Button-3>", self.on_right_click)

        self.drag_offset_x = 0
        self.drag_offset_y = 0

    # ---------------------------------------------------------
    # Tekst
    # ---------------------------------------------------------
    def get_value_label(self):
        if self.ctype == "GND":
            return ""
        if self.is_source:
            return f"{self.voltage_raw:.2f}V / {self.frequency_raw:.2f}Hz"
        if self.ctype == "R":
            return f"{self.value_raw:.2f}Ω"
        if self.ctype == "L":
            return f"{self.value_raw:.2f}mH"
        if self.ctype == "C":
            return f"{self.value_raw:.2f}µF"
        return ""

    # ---------------------------------------------------------
    # Port visibility
    # ---------------------------------------------------------
    def show_ports(self):
        for p in self.ports:
            self.canvas.itemconfigure(p.id, state="normal")

    def hide_ports(self):
        for p in self.ports:
            self.canvas.itemconfigure(p.id, state="hidden")

    # ---------------------------------------------------------
    # Drag
    # ---------------------------------------------------------
    def on_click(self, event):
        if self.canvas.editor.wire_mode:
            return
        self.drag_offset_x = event.x - self.x
        self.drag_offset_y = event.y - self.y

    def on_drag(self, event):
        if self.canvas.editor.wire_mode:
            return

        new_x = round((event.x - self.drag_offset_x) / GRID) * GRID
        new_y = round((event.y - self.drag_offset_y) / GRID) * GRID

        # AC‑kilde skal være centreret
        if self.is_source:
            new_x -= 30
            new_y -= 30

        dx = new_x - self.x
        dy = new_y - self.y

        for item in self.items + self.text_items:
            self.canvas.move(item, dx, dy)

        self.x = new_x
        self.y = new_y

        for p in self.ports:
            p.update()

        for p in self.ports:
            if hasattr(p, "wires"):
                for w in p.wires:
                    w.update()

    # ---------------------------------------------------------
    # Delete
    # ---------------------------------------------------------
    def delete(self):
        for p in self.ports:
            if hasattr(p, "wires"):
                for w in p.wires[:]:
                    w.delete()

        for item in self.items + self.text_items:
            self.canvas.delete(item)

    # ---------------------------------------------------------
    # Right-click
    # ---------------------------------------------------------
    def on_right_click(self, event):
        self.canvas.editor.selected_component = self
        self.canvas.editor.component_menu.tk_popup(event.x_root, event.y_root)
    def edit_properties(self):
        if self.ctype == "GND":
            return

        if self.is_source:
            v = simpledialog.askfloat("AC-kilde", "Spænding (V):", initialvalue=self.voltage_raw)
            if v is None:
                return
            f = simpledialog.askfloat("AC-kilde", "Frekvens (Hz):", initialvalue=self.frequency_raw)
            if f is None:
                return

            self.voltage_raw = v
            self.frequency_raw = f
            self.voltage_si = v
            self.frequency_si = f

        else:
            if self.ctype == "R":
                v = simpledialog.askfloat("Modstand", "Modstand (ohm):", initialvalue=self.value_raw)
                if v is None:
                    return
                self.value_raw = v
                self.value_si = v

            elif self.ctype == "L":
                v = simpledialog.askfloat("Spole", "Induktans (mH):", initialvalue=self.value_raw)
                if v is None:
                    return
                self.value_raw = v
                self.value_si = v / 1000.0

            elif self.ctype == "C":
                v = simpledialog.askfloat("Kondensator", "Kapacitans (µF):", initialvalue=self.value_raw)
                if v is None:
                    return
                self.value_raw = v
                self.value_si = v * 1e-6

        if hasattr(self, "value_text_id") and self.value_text_id:
            self.canvas.itemconfigure(self.value_text_id, text=self.get_value_label())

# ---------------------------------------------------------
# EDITOR
# ---------------------------------------------------------
class Editor:
    def __init__(self, parent):
        self.root = parent
        self.wire_style = 1  # 1 = ét knæk, 2 = to knæk
        self.show_handles = True

        # Toolbar
        self.toolbar = tk.Frame(parent)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        self.btn_r = tk.Button(self.toolbar, text="R", command=lambda: self.set_mode("R"))
        self.btn_l = tk.Button(self.toolbar, text="L", command=lambda: self.set_mode("L"))
        self.btn_c = tk.Button(self.toolbar, text="C", command=lambda: self.set_mode("C"))
        self.btn_ac = tk.Button(self.toolbar, text="AC", command=lambda: self.set_mode("AC"))
        self.btn_gnd = tk.Button(self.toolbar, text="GND", command=lambda: self.set_mode("GND"))
        self.btn_wire1 = tk.Button(self.toolbar, text="Wire 1-knæk", command=lambda: self.set_wire_style(1))
        self.btn_wire2 = tk.Button(self.toolbar, text="Wire 2-knæk", command=lambda: self.set_wire_style(2))
        self.chk_handles_var = tk.BooleanVar(value=True)
        self.chk_handles = tk.Checkbutton(
            self.toolbar,
            text="Vis knæk‑punkter",
            variable=self.chk_handles_var,
            command=self.toggle_handles
        )
  



        self.btn_sim = tk.Button(self.toolbar, text="Simulér AC", command=self.simulate_ac)

        self.btn_r.pack(side=tk.LEFT)
        self.btn_l.pack(side=tk.LEFT)
        self.btn_c.pack(side=tk.LEFT)
        self.btn_ac.pack(side=tk.LEFT)
        self.btn_gnd.pack(side=tk.LEFT)
        self.btn_wire1.pack(side=tk.LEFT)
        self.btn_wire2.pack(side=tk.LEFT)
        self.chk_handles.pack(side=tk.LEFT)
        self.btn_sim.pack(side=tk.RIGHT)

        # Canvas
        self.canvas = tk.Canvas(parent, bg="white", width=1000, height=700)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.editor = self

        self.canvas.bind_class("Canvas", "<Button-1>", self.on_canvas_click)


        # Data
        self.components = []
        self.wires = []
        self.mode = None
        self.wire_mode = False
        self.pending_port = None
        self.selected_component = None

        self.r_count = 0
        self.l_count = 0
        self.c_count = 0
        self.ac_count = 0
        self.gnd_count = 0

        # Right-click menu
        self.component_menu = tk.Menu(self.root, tearoff=0)
        # Wire menu
        self.wire_menu = tk.Menu(self.root, tearoff=0)
        self.wire_menu.add_command(label="Reset layout", command=self.reset_selected_wire)
        self.wire_menu.add_command(label="Slet wire", command=self.delete_selected_wire)

        self.selected_wire = None

        self.component_menu.add_command(label="Egenskaber", command=self.edit_selected_properties)
        self.component_menu.add_command(label="Slet", command=self.delete_selected_component)

        self.draw_grid()
    def set_wire_style(self, style):
        self.wire_style = style
        self.set_mode("WIRE")

    def reset_selected_wire(self):
        if self.selected_wire:
            self.selected_wire.reset_layout()

    def delete_selected_wire(self):
        if self.selected_wire:
            self.selected_wire.delete()
            self.selected_wire = None
    def toggle_handles(self):
        self.show_handles = self.chk_handles_var.get()

        for w in self.wires:
            for h in w.handles:
                state = "normal" if self.show_handles else "hidden"
                self.canvas.itemconfigure(h, state=state)
    # ---------------------------------------------------------
    # Grid
    # ---------------------------------------------------------
    def draw_grid(self):
        for x in range(0, 2000, GRID):
            self.canvas.create_line(x, 0, x, 2000, fill="#f0f0f0")
        for y in range(0, 2000, GRID):
            self.canvas.create_line(0, y, 2000, y, fill="#f0f0f0")

    # ---------------------------------------------------------
    # Mode
    # ---------------------------------------------------------
    def set_mode(self, mode):
        # Wire mode toggles port visibility
        if mode == "WIRE":
            self.wire_mode = True
            self.mode = "WIRE"
            for c in self.components:
                c.show_ports()
            return

        # Leaving wire mode
        if self.wire_mode:
            self.wire_mode = False
            self.pending_port = None
            for c in self.components:
                c.hide_ports()

        # Component placement mode (one-shot)
        self.mode = mode

    # ---------------------------------------------------------
    # Navngivning
    # ---------------------------------------------------------
    def get_next_name(self, ctype):
        if ctype == "R":
            self.r_count += 1
            return f"R_{self.r_count}"
        if ctype == "L":
            self.l_count += 1
            return f"L_{self.l_count}"
        if ctype == "C":
            self.c_count += 1
            return f"C_{self.c_count}"
        if ctype == "AC":
            self.ac_count += 1
            return f"AC_{self.ac_count}"
        if ctype == "GND":
            self.gnd_count += 1
            return f"GND_{self.gnd_count}"
        return "X"

    # ---------------------------------------------------------
    # Canvas click
    # ---------------------------------------------------------
    def on_canvas_click(self, event):
        # Wire placement
        if self.wire_mode:
            clicked_port = self.find_port_at(event.x, event.y)

            if clicked_port:
                if self.pending_port is None:
                    self.pending_port = clicked_port
                else:
                    if clicked_port is not self.pending_port:
                        w = Wire(self.canvas, self.pending_port, clicked_port, style=self.wire_style)
                        self.wires.append(w)
                    self.pending_port = None
                return

            # Exit wire mode if clicking empty space
            self.wire_mode = False
            self.pending_port = None
            for c in self.components:
                c.hide_ports()
            self.mode = None
            return

        # Component placement (ONE-SHOT)
        if self.mode in ("R", "L", "C", "AC", "GND"):
            comp = Component(self.canvas, self, self.mode, event.x, event.y,
                             is_source=(self.mode == "AC"))
            self.components.append(comp)

            # One-shot: reset mode after placing ONE component
            self.mode = None
            return

    # ---------------------------------------------------------
    # Port detection
    # ---------------------------------------------------------
    def find_port_at(self, x, y):
        for c in self.components:
            for p in c.ports:
                if abs(p.x - x) <= 6 and abs(p.y - y) <= 6:
                    return p
        return None

    # ---------------------------------------------------------
    # Right-click actions
    # ---------------------------------------------------------
    def edit_selected_properties(self):
        if self.selected_component:
            self.selected_component.edit_properties()

    def delete_selected_component(self):
        if self.selected_component:
            self.selected_component.delete()
            self.components.remove(self.selected_component)
            self.selected_component = None
    

    # ---------------------------------------------------------
    # CLEANUP PATCH
    # ---------------------------------------------------------
    def cleanup(self):
        valid_ports = {p for c in self.components for p in c.ports}

        dead_wires = []
        for w in self.wires:
            if w.port_a not in valid_ports or w.port_b not in valid_ports:
                dead_wires.append(w)

        for w in dead_wires:
            w.delete()

    # ---------------------------------------------------------
    # AC simulation
    # ---------------------------------------------------------
    def simulate_ac(self):
        try:
            self.cleanup()
            data = self.extract_circuit_data()
        except Exception as e:
            messagebox.showerror("Fejl", f"Kunne ikke udtrække kredsløbsdata:\n{e}")
            return

        try:
            solver = ACSolver(data)
            results = solver.solve()
        except Exception as e:
            messagebox.showerror("Fejl i solver", f"Der opstod en fejl i AC-beregningen:\n{e}")
            return

        self.show_results_popup(results)

    # ---------------------------------------------------------
    # Node extraction (GND = node 0)
    # ---------------------------------------------------------
    def extract_circuit_data(self):
        ports = []
        for c in self.components:
            for p in c.ports:
                ports.append(p)

        parent = {id(p): id(p) for p in ports}

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        def union(a, b):
            ra = find(a)
            rb = find(b)
            if ra != rb:
                parent[rb] = ra

        # Ignore dead wires
        for w in self.wires:
            if w.port_a not in ports or w.port_b not in ports:
                continue
            union(id(w.port_a), id(w.port_b))

        groups = {}
        for p in ports:
            r = find(id(p))
            groups.setdefault(r, []).append(p)

        gnd_component = next((c for c in self.components if c.ctype == "GND"), None)
        gnd_port = gnd_component.ports[0] if gnd_component else None

        next_node = 0

        for root_id, plist in groups.items():
            if gnd_port and gnd_port in plist:
                nid = 0
            else:
                next_node += 1
                nid = next_node

            for p in plist:
                p.node_id = nid

        components_data = []
        frequency = 0.0

        for c in self.components:
            if c.ctype == "GND":
                continue

            if c.ctype in ("R", "L", "C"):
                n1 = c.ports[0].node_id
                n2 = c.ports[1].node_id

            elif c.ctype == "AC":
                n1 = c.ports[0].node_id
                n2 = c.ports[1].node_id
                frequency = c.frequency_si

            if n1 is None or n2 is None:
                raise ValueError(f"Komponent {c.name} er ikke fuldt forbundet.")

            if c.ctype == "AC":
                components_data.append({
                    "name": c.name,
                    "type": "AC",
                    "n1": n1,
                    "n2": n2,
                    "voltage": c.voltage_si,
                    "frequency": c.frequency_si
                })

            elif c.ctype == "R":
                components_data.append({
                    "name": c.name,
                    "type": "R",
                    "n1": n1,
                    "n2": n2,
                    "value": c.value_si
                })

            elif c.ctype == "L":
                components_data.append({
                    "name": c.name,
                    "type": "L",
                    "n1": n1,
                    "n2": n2,
                    "value": c.value_si
                })

            elif c.ctype == "C":
                components_data.append({
                    "name": c.name,
                    "type": "C",
                    "n1": n1,
                    "n2": n2,
                    "value": c.value_si
                })

        if frequency == 0:
            raise ValueError("Ingen AC-kilde fundet.")
        print("=== DEBUG: NODE LIST ===")
        for c in self.components:
            print(f"{c.name}:")
            for i, p in enumerate(c.ports):
                print(f"  Port {i}: node_id={p.node_id}, x={p.x}, y={p.y}")

        print("=== DEBUG: WIRES ===")
        for w in self.wires:
            print(f"Wire: {w.port_a.node_id} <-> {w.port_b.node_id}")
        return {
            "components": components_data,
            "frequency": frequency
        }

    # ---------------------------------------------------------
    # Resultat-popup
    # ---------------------------------------------------------
    def show_results_popup(self, results):
        win = tk.Toplevel(self.root)
        win.title("AC-resultater")

        text = tk.Text(win, width=60, height=30)
        text.pack(fill=tk.BOTH, expand=True)

        node_voltages = results.get("node_voltages", {})
        comp_currents = results.get("component_currents", {})
        z_total = results.get("total_impedance", None)
        i_total = results.get("total_current", None)
        comp_voltages = results.get("component_voltages", {})
        def fmt_complex(z):
            if z is None:
                return "N/A"
            mag = abs(z)
            ang = math.degrees(math.atan2(z.imag, z.real))
            return f"{mag:.3f} ∠ {ang:.1f}°"

        text.insert(tk.END, "Node-spændinger:\n")
        for nid, v in node_voltages.items():
            text.insert(tk.END, f"  Node {nid}: {fmt_complex(v)} V\n")

        text.insert(tk.END, "\nStrøm gennem komponenter:\n")
        for name, i in comp_currents.items():
            text.insert(tk.END, f"  {name}: {fmt_complex(i)} A\n")
        text.insert(tk.END, "\nSpænding over komponenter:\n")
        for name, v in comp_voltages.items():
            text.insert(tk.END, f"  {name}: {fmt_complex(v)} V\n")


        text.insert(tk.END, "\nTotal impedans og strøm:\n")
        text.insert(tk.END, f"  Z_total: {fmt_complex(z_total)} Ω\n")
        text.insert(tk.END, f"  I_total: {fmt_complex(i_total)} A\n")
                # ---------------------------------------------------------
        # EKSPORT-KNAP (placeret i popup-vinduet)
        # ---------------------------------------------------------
        def export_vectors():
            # Vælg fil
            path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt")]
            )
            if not path:
                return

            # Hjælpefunktion: konverter kompleks → (x,y)
            def cart(z):
                return z.real, z.imag

            try:
                with open(path, "w") as f:

                    # Total strøm
                    if i_total is not None:
                        I_plot = -i_total
                        x, y = cart(I_plot)
                        f.write(f"VECTOR 0 0 {x:.6f} {y:.6f} green I_total 0.2 0.2 solid\n")

                    # Spændingsvektorer
                    for name, v in comp_voltages.items():
                        x, y = cart(v)
                        f.write(f"VECTOR 0 0 {x:.6f} {y:.6f} blue {name}_V 0.2 0.2 solid\n")

                    # Strømvektor
                    for name, i in comp_currents.items():
                        # Vend AC-kildens strøm
                        if name.startswith("AC_"):
                            i = -i
                        x, y = cart(i)
                        f.write(f"VECTOR 0 0 {x:.6f} {y:.6f} red {name}_I 0.2 0.2 solid\n")

                messagebox.showinfo("Eksporteret", "Vektordiagram er eksporteret i VectorTab-format.")

            except Exception as e:
                messagebox.showerror("Fejl", f"Kunne ikke eksportere vektorer:\n{e}")

        # Knap nederst i popup
        btn_frame = tk.Frame(win)
        btn_frame.pack(fill=tk.X, pady=5)

        export_btn = tk.Button(btn_frame, text="Eksporter vektordiagram til VectorTab", command=export_vectors)
        export_btn.pack(side=tk.RIGHT, padx=10)


class ACTab:
    def __init__(self, parent):
        self.frame = tk.Frame(parent)
        self.editor = Editor(self.frame)


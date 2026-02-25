import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog
import re
from netlist_3phase import Netlist3Phase
from solver_3phase import solve_3phase
import math
import cmath


class AC3Tab:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)

        # Netlist objekt
        self.netlist = Netlist3Phase()

        # Toolbar
        self.current_tool = None
        self._build_toolbar()

        # Dashboard (komponent-liste)
        self._build_component_dashboard()

        # Variabler til fase-input
        self.voltage_var = {}
        self.angle_var = {}
        self.freq_var = {}

        # Canvas-område
        self.canvas = tk.Canvas(self.frame, width=900, height=600, bg="white")
        self.canvas.pack(fill="both", expand=True)

        # Node rækkefølge
        self.nodes = ["L1", "L2", "L3", "N"]

        # Y-positioner for linjerne
        self.node_y = {}

        # Slotsystem
        self.slots = []
        self.slot_map = {}
        self.slot_clicks = []

        # Byg UI-rækker
        self._build_phase_rows()

        # Klik-registrering
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Button-3>", self.on_right_click)

        # Reflow dashboard
        self.dashboard_inner.bind("<Configure>", self._on_dashboard_configure)
        self.dashboard_container.bind("<Configure>", lambda e: self._reflow_component_boxes())

    # ---------------------------------------------------------
    # Toolbar
    # ---------------------------------------------------------
    def _build_toolbar(self):
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(fill="x")

        ttk.Button(toolbar, text="Modstand", command=lambda: self.set_tool("R")).pack(side="left")
        ttk.Button(toolbar, text="Spole", command=lambda: self.set_tool("L")).pack(side="left")
        ttk.Button(toolbar, text="Kondensator", command=lambda: self.set_tool("C")).pack(side="left")
        ttk.Button(toolbar, text="Simulate", command=self.run_solver).pack(side="right")

    def set_tool(self, tool):
        if getattr(self, "inline_edit_active", False):
            return
        self.current_tool = tool
        self.slot_clicks = []
        self.show_slots()

    # ---------------------------------------------------------
    # Dashboard
    # ---------------------------------------------------------
    def _build_component_dashboard(self):
        self.dashboard_container = ttk.Frame(self.frame)
        self.dashboard_container.pack(fill="x", pady=(4, 2))

        self.dashboard_canvas = tk.Canvas(self.dashboard_container, height=90)
        self.dashboard_canvas.pack(side="left", fill="x", expand=True)

        self.dashboard_scrollbar = ttk.Scrollbar(
            self.dashboard_container,
            orient="vertical",
            command=self.dashboard_canvas.yview
        )
        self.dashboard_scrollbar.pack(side="right", fill="y")

        self.dashboard_canvas.configure(yscrollcommand=self.dashboard_scrollbar.set)

        self.dashboard_inner = ttk.Frame(self.dashboard_canvas)
        self.dashboard_canvas.create_window((0, 0), window=self.dashboard_inner, anchor="nw")

        self.component_boxes = {}
        self.inline_edit_active = False

    def _on_dashboard_configure(self, event):
        self.dashboard_canvas.configure(scrollregion=self.dashboard_canvas.bbox("all"))

    def _reflow_component_boxes(self):
        if not self.component_boxes:
            return

        total_width = self.dashboard_container.winfo_width()
        if total_width <= 0:
            return

        box_width = 150
        cols = max(1, total_width // box_width)

        names = list(self.component_boxes.keys())

        for child in self.dashboard_inner.winfo_children():
            child.grid_forget()

        for idx, name in enumerate(names):
            col = idx // 3
            row = idx % 3
            self.component_boxes[name].grid(row=row, column=col, padx=4, pady=2, sticky="nw")

    # ---------------------------------------------------------
    # Enhedsfunktion
    # ---------------------------------------------------------
    def _unit_for(self, ctype):
        return {
            "R": "Ω",
            "L": "mH",
            "C": "µF"
        }.get(ctype, "")

    # ---------------------------------------------------------
    # Navne-validering
    # ---------------------------------------------------------
    def _valid_name(self, text):
        return re.fullmatch(r"[A-Za-z][0-9]{1,2}", text) is not None

    # ---------------------------------------------------------
    # Opret komponentboks
    # ---------------------------------------------------------
    def _create_component_box(self, name):
        comp = self.netlist.components.get(name)
        if not comp:
            return

        frame = ttk.Frame(self.dashboard_inner, relief="solid", borderwidth=1, padding=(4, 2))

        lbl_name = ttk.Label(frame, text=name, width=6, anchor="w")
        lbl_name.grid(row=0, column=0, sticky="w")

        value_str = str(comp.get("value", ""))
        lbl_value = ttk.Label(frame, text=value_str, width=6, anchor="w")
        lbl_value.grid(row=0, column=1, sticky="w", padx=(4, 0))

        lbl_unit = ttk.Label(frame, text=self._unit_for(comp["type"]), width=4, anchor="w")
        lbl_unit.grid(row=0, column=2, sticky="w")

        frame._name_label = lbl_name
        frame._value_label = lbl_value
        frame._unit_label = lbl_unit

        lbl_name.bind("<Button-1>", lambda e, n=name: self._start_inline_edit(n, field="name"))
        lbl_value.bind("<Button-1>", lambda e, n=name: self._start_inline_edit(n, field="value"))

        self.component_boxes[name] = frame
        self._reflow_component_boxes()

    # ---------------------------------------------------------
    # Inline-edit
    # ---------------------------------------------------------
    def _start_inline_edit(self, name, field):
        if self.inline_edit_active:
            return
        if name not in self.component_boxes:
            return

        frame = self.component_boxes[name]

        if field == "name":
            label = frame._name_label
            old_value = label.cget("text")
        else:
            label = frame._value_label
            old_value = label.cget("text")

        entry = ttk.Entry(frame, width=6)
        entry.insert(0, old_value)
        entry.select_range(0, "end")
        entry.focus_set()

        col = 0 if field == "name" else 1
        label.grid_forget()
        entry.grid(row=0, column=col, sticky="w")

        self.inline_edit_active = True

        def finish(save):
            entry.grid_forget()
            label.grid(row=0, column=col, sticky="w")

            if not save:
                self.inline_edit_active = False
                return

            new_val = entry.get().strip()

            if field == "name":
                old_name = name
                new_name = new_val.upper()

                if not self._valid_name(new_name):
                    self.inline_edit_active = False
                    return

                # Opdater netlist
                self.netlist.rename_component(old_name, new_name)

                # Opdater canvas-tekst (find text-objekter)
                comp = self.netlist.components.get(new_name, {})
                for cid in comp.get("canvas_ids", []):
                    try:
                        if self.canvas.type(cid) == "text":
                            self.canvas.itemconfig(cid, text=new_name)
                    except tk.TclError:
                        pass

                # Opdater dashboard mapping og label
                frame = self.component_boxes.pop(old_name)
                self.component_boxes[new_name] = frame
                frame._name_label.config(text=new_name)

                # Reflow dashboard
                self._reflow_component_boxes()
            else:
                label.config(text=new_val)
                if name in self.netlist.components:
                    self.netlist.components[name]["value"] = new_val

            self.inline_edit_active = False

        entry.bind("<Return>", lambda e: finish(True))
        entry.bind("<Escape>", lambda e: finish(False))

    # ---------------------------------------------------------
    # Highlight
    # ---------------------------------------------------------
    def _highlight_component(self, name):
        comp = self.netlist.components.get(name)
        if not comp:
            return

        for other_name, other_comp in self.netlist.components.items():
            for cid in other_comp.get("canvas_ids", []):
                try:
                    self.canvas.itemconfig(cid, width=2, outline="black")
                except tk.TclError:
                    pass

        for cid in comp.get("canvas_ids", []):
            try:
                self.canvas.itemconfig(cid, width=3, outline="red")
            except tk.TclError:
                pass

    # ---------------------------------------------------------
    # Fase-rækker
    # ---------------------------------------------------------
    def _build_phase_rows(self):
        y_offset = 100
        start_y = 80

        for i, node in enumerate(self.nodes):
            y = start_y + i * y_offset

            self.canvas.create_text(40, y, text=node, anchor="w", font=("Arial", 12, "bold"))
            self.canvas.create_line(100, y, 850, y, width=2)
            self.node_y[node] = y

            if node != "N":
                vy = y + 18

                if node not in self.voltage_var:
                    self.voltage_var[node] = tk.DoubleVar(value=230.0)
                    self.angle_var[node] = tk.DoubleVar(value=0.0)
                    self.freq_var[node] = tk.DoubleVar(value=50.0)

                small_font = ("Arial", 8)

                v_entry = ttk.Entry(self.frame, textvariable=self.voltage_var[node], width=6)
                v_entry.configure(font=small_font)
                self.canvas.create_window(15, vy, window=v_entry, anchor="w")

                a_entry = ttk.Entry(self.frame, textvariable=self.angle_var[node], width=4)
                a_entry.configure(font=small_font)
                self.canvas.create_window(15, vy + 20, window=a_entry, anchor="w")

                f_entry = ttk.Entry(self.frame, textvariable=self.freq_var[node], width=5)
                f_entry.configure(font=small_font)
                self.canvas.create_window(15, vy + 40, window=f_entry, anchor="w")

                self.canvas.create_text(80, vy, text="V", anchor="e", font=small_font)
                self.canvas.create_text(80, vy + 20, text="°", anchor="e", font=small_font)
                self.canvas.create_text(80, vy + 40, text="Hz", anchor="e", font=small_font)

    # ---------------------------------------------------------
    # Slots
    # ---------------------------------------------------------
    def show_slots(self):
        for s in self.slots:
            self.canvas.delete(s)
        self.slots.clear()
        self.slot_map.clear()

        if not self.current_tool:
            return

        x_start = 150
        x_step = 60

        for node in self.nodes:
            y = self.node_y[node]
            for i in range(10):
                x = x_start + i * x_step
                slot = self.canvas.create_oval(
                    x - 4, y - 4,
                    x + 4, y + 4,
                    fill="white", outline="black"
                )
                self.slots.append(slot)
                self.slot_map[slot] = (node, x, y)

    def _detect_slot(self, x_click, y_click):
        if not self.slots:
            return None
        cid = self.canvas.find_closest(x_click, y_click)[0]
        return self.slot_map.get(cid, None)

    # ---------------------------------------------------------
    # Klik-håndtering
    # ---------------------------------------------------------
    def on_canvas_click(self, event):
        if self.inline_edit_active:
            return
        if not self.current_tool:
            return

        slot = self._detect_slot(event.x, event.y)
        if not slot:
            return

        self.slot_clicks.append(slot)

        if len(self.slot_clicks) == 2:
            (nodeA, xA, yA), (nodeB, xB, yB) = self.slot_clicks
            self.slot_clicks = []

            if self.current_tool in ("R", "L", "C"):
                self.place_simple_component(self.current_tool, nodeA, nodeB, xA, yA, xB, yB)

            for s in self.slots:
                self.canvas.delete(s)
            self.slots.clear()
            self.slot_map.clear()

    # ---------------------------------------------------------
    # Placering af komponenter (IEC-symboler)
    # ---------------------------------------------------------
    def place_simple_component(self, ctype, n1, n2, xA, yA, xB, yB):
        name = self.netlist.add_component(ctype, n1, n2)

        if yA < yB:
            top_x, top_y = xA, yA
            bottom_x, bottom_y = xB, yB
        else:
            top_x, top_y = xB, yB
            bottom_x, bottom_y = xA, yA

        comp_y = top_y + 15
        comp_x = (xA + xB) / 2

        canvas_ids = []

        # R: rektangel
        if ctype == "R":
            box = self.canvas.create_rectangle(
                comp_x - 20, comp_y - 10,
                comp_x + 20, comp_y + 10,
                fill="lightgray"
            )
            canvas_ids.append(box)
            label = self.canvas.create_text(comp_x, comp_y, text=name)
            canvas_ids.append(label)

        # L: IEC-spole (buer)
        elif ctype == "L":
            # 3 halvcirkler
            radius = 6
            start_x = comp_x - 18
            for i in range(3):
                x0 = start_x + i * (radius * 2)
                y0 = comp_y - radius
                x1 = x0 + 2 * radius
                y1 = comp_y + radius
                arc = self.canvas.create_arc(
                    x0, y0, x1, y1,
                    start=180, extent=180,
                    style=tk.ARC, width=2
                )
                canvas_ids.append(arc)
            label = self.canvas.create_text(comp_x, comp_y + 14, text=name)
            canvas_ids.append(label)

        # C: IEC-kondensator (to plader)
        elif ctype == "C":
            plate_offset = 5
            plate_height = 10

            # Venstre plade
            plate1 = self.canvas.create_line(
                comp_x - plate_offset, comp_y - plate_height,
                comp_x - plate_offset, comp_y + plate_height,
                width=2
            )

            # Højre plade
            plate2 = self.canvas.create_line(
                comp_x + plate_offset, comp_y - plate_height,
                comp_x + plate_offset, comp_y + plate_height,
                width=2
            )

            # Venstre pind
            pin_left = self.canvas.create_line(
                comp_x - 20, comp_y,
                comp_x - plate_offset, comp_y,
                width=2
            )

            # Højre pind
            pin_right = self.canvas.create_line(
                comp_x + plate_offset, comp_y,
                comp_x + 20, comp_y,
                width=2
            )

            canvas_ids.extend([plate1, plate2, pin_left, pin_right])

            # Navn under symbolet
            label = self.canvas.create_text(comp_x, comp_y + 14, text=name)
            canvas_ids.append(label)


        else:
            # fallback: rektangel
            box = self.canvas.create_rectangle(
                comp_x - 20, comp_y - 10,
                comp_x + 20, comp_y + 10,
                fill="lightgray"
            )
            canvas_ids.append(box)
            label = self.canvas.create_text(comp_x, comp_y, text=name)
            canvas_ids.append(label)

        # Forbindelser til faser
        wire1 = self.canvas.create_line(top_x, top_y, top_x, comp_y, width=2)
        wire2 = self.canvas.create_line(top_x, comp_y, comp_x - 20, comp_y, width=2)
        wire3 = self.canvas.create_line(comp_x + 20, comp_y, bottom_x, comp_y, width=2)
        wire4 = self.canvas.create_line(bottom_x, comp_y, bottom_x, bottom_y, width=2)

        dotA = self.canvas.create_oval(top_x - 3, top_y - 3, top_x + 3, top_y + 3, fill="black")
        dotB = self.canvas.create_oval(bottom_x - 3, bottom_y - 3, bottom_x + 3, bottom_y + 3, fill="black")

        canvas_ids.extend([wire1, wire2, wire3, wire4, dotA, dotB])

        self.netlist.attach_canvas_ids(name, *canvas_ids)

        self._create_component_box(name)

    # ---------------------------------------------------------
    # Højreklik-menu
    # ---------------------------------------------------------
    def on_right_click(self, event):
        if self.inline_edit_active:
            return

        clicked = self.netlist.find_component_by_canvas_id(event.x, event.y, self.canvas)
        if not clicked:
            return

        menu = tk.Menu(self.frame, tearoff=0)
        menu.add_command(label="Slet", command=lambda: self.delete_component(clicked))
        menu.post(event.x_root, event.y_root)

    # ---------------------------------------------------------
    # Sletning og redraw
    # ---------------------------------------------------------
    def delete_component(self, name):
        # 1) Slet canvas-objekter for den komponent
        comp = self.netlist.components.get(name)
        if comp:
            for cid in comp.get("canvas_ids", []):
                try:
                    self.canvas.delete(cid)
                except tk.TclError:
                    pass

        # 2) Fjern fra netlisten
        self.netlist.components.pop(name, None)

        # 3) Fjern fra dashboard
        if name in self.component_boxes:
            self.component_boxes[name].destroy()
            self.component_boxes.pop(name)

        # 4) Reflow dashboard-layout
        self._reflow_component_boxes()


    def redraw(self):
        # 1) Slet ALT på canvas
        self.canvas.delete("all")

        # 2) Genskab fase-linjer
        self._build_phase_rows()

        # 3) Genskab alle komponenter på canvas
        self.netlist.redraw_all(self.canvas, self.node_y)

        # 4) Ryd dashboard HELT (destroy, ikke grid_forget)
        for child in self.dashboard_inner.winfo_children():
            child.destroy()

        # 5) Ryd mapping
        self.component_boxes.clear()

        # 6) Genskab dashboard-bokse for alle eksisterende komponenter
        for name in self.netlist.components.keys():
            self._create_component_box(name)


    # ---------------------------------------------------------
    # Solver
    # ---------------------------------------------------------
    def run_solver(self):
        # 1) Byg komplekse fase-spændinger fra GUI
        phases = {}
        for node in ("L1", "L2", "L3"):
            V_mag = self.voltage_var[node].get()
            ang_deg = self.angle_var[node].get()
            f = self.freq_var[node].get()

            ang_rad = math.radians(ang_deg)
            V_complex = cmath.rect(V_mag, ang_rad)

            phases[node] = {"V": V_complex, "f": f}

        phases["N"] = {"V": 0+0j, "f": phases["L1"]["f"]}

        # 2) Kald solver
        results = solve_3phase(self.netlist, phases)

        # 3) Tilføj spændinger til popup (til linjespændinger)
        results["V"] = {
            "L1": phases["L1"]["V"],
            "L2": phases["L2"]["V"],
            "L3": phases["L3"]["V"],
            "N": 0+0j
        }

        # 4) Vis popup
        self.show_results_popup(results)

    def show_results_popup(self, results):
        win = tk.Toplevel(self.frame)
        win.title("3-faset AC-resultater")

        text = tk.Text(win, width=70, height=35, font=("Consolas", 10))
        text.pack(fill=tk.BOTH, expand=True)
        def export_vectors():
            path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt")]
            )
            if not path:
                return

            def cart(z):
                return z.real, z.imag

            try:
                with open(path, "w") as f:

                    # -------------------------------------------------
                    # 1) FASESPÆNDINGER (U_L1, U_L2, U_L3)
                    # -------------------------------------------------
                    for ph, V in results["V"].items():
                        if ph == "N":
                            continue
                        x, y = cart(V)  # 1 volt = 1 enhed
                        f.write(f"VECTOR 0 0 {x:.6f} {y:.6f} blue U_{ph} 0.2 0.2 solid\n")

                    # -------------------------------------------------
                    # 2) LINJESPÆNDINGER (U_L1L2, U_L2L3, U_L3L1)
                    # -------------------------------------------------
                    V = results["V"]
                    line_voltages = {
                        "L1L2": V["L1"] - V["L2"],
                        "L2L3": V["L2"] - V["L3"],
                        "L3L1": V["L3"] - V["L1"],
                    }

                    for name, v in line_voltages.items():
                        x, y = cart(v)
                        f.write(f"VECTOR 0 0 {x:.6f} {y:.6f} green U_{name} 0.2 0.2 solid\n")

                    # -------------------------------------------------
                    # 3) FASESTRØMME (I_L1, I_L2, I_L3, I_N)
                    # -------------------------------------------------
                    for ph, I in results["I"].items():
                        x, y = cart(I)
                        f.write(f"VECTOR 0 0 {x:.6f} {y:.6f} red I_{ph} 0.2 0.2 solid\n")

                    # -------------------------------------------------
                    # 4) NEGATIVE STRØMME (-I_L1, -I_L2, -I_L3, -I_N)
                    # -------------------------------------------------
                    for ph, I in results["I"].items():
                        x, y = cart(-I)
                        f.write(f"VECTOR 0 0 {x:.6f} {y:.6f} orange I_{ph}_neg 0.2 0.2 solid\n")

                messagebox.showinfo("Eksporteret", "Vektordiagram er eksporteret i VectorTab-format.")

            except Exception as e:
                messagebox.showerror("Fejl", f"Kunne ikke eksportere vektorer:\n{e}")


        scrollbar = tk.Scrollbar(text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=text.yview)

        def fmt_complex(z):
            mag = abs(z)
            ang = math.degrees(cmath.phase(z))
            return f"{mag:.3f} ∠ {ang:.1f}°"

        I = results["I"]
        S = results["S"]
        cosphi = results["cosphi"]

        # ---------------------------------------------------------
        # STRØMME
        # ---------------------------------------------------------
        text.insert(tk.END, "=== STRØMME ===\n")
        text.insert(tk.END, f"  I_L1 : {fmt_complex(I['L1'])} A\n")
        text.insert(tk.END, f"  I_L2 : {fmt_complex(I['L2'])} A\n")
        text.insert(tk.END, f"  I_L3 : {fmt_complex(I['L3'])} A\n")
        text.insert(tk.END, f"  I_N  : {fmt_complex(I['N'])} A\n")

        text.insert(tk.END, "\n")

        # ---------------------------------------------------------
        # EFFEKT
        # ---------------------------------------------------------
        text.insert(tk.END, "=== EFFEKT PR. FASE ===\n")
        for ph in ("L1", "L2", "L3"):
            S_mag = abs(S[ph])
            P = S[ph].real
            Q = S[ph].imag
            text.insert(tk.END, f"{ph}:\n")
            text.insert(tk.END, f"  S = {S_mag:.3f} VA\n")
            text.insert(tk.END, f"  P = {P:.3f} W\n")
            text.insert(tk.END, f"  Q = {Q:.3f} var\n")
            text.insert(tk.END, f"  cos(φ) = {cosphi[ph]:.3f}\n\n")

        # ---------------------------------------------------------
        # LINJESPÆNDINGER (ekstra lækkert)
        # ---------------------------------------------------------
        text.insert(tk.END, "=== LINJESPÆNDINGER ===\n")
        V = results["V"]  # vi tilføjer dette i run_solver
        text.insert(tk.END, f"  V_L1L2 = {fmt_complex(V['L1'] - V['L2'])} V\n")
        text.insert(tk.END, f"  V_L2L3 = {fmt_complex(V['L2'] - V['L3'])} V\n")
        text.insert(tk.END, f"  V_L3L1 = {fmt_complex(V['L3'] - V['L1'])} V\n")

        btn_frame = tk.Frame(win)
        btn_frame.pack(fill=tk.X, pady=5)
        export_btn = tk.Button(btn_frame, text="Eksporter vektordiagram til VectorTab", command=export_vectors)
        export_btn.pack(side=tk.RIGHT, padx=10)

        
# Standalone test
if __name__ == "__main__":
    root = tk.Tk()
    root.title("AC3 Editor")
    app = AC3Tab(root)
    app.frame.pack(fill="both", expand=True)
    root.mainloop()

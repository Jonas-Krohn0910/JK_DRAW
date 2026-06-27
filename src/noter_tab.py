import tkinter as tk
from tkinter import ttk
import os
import fitz
from PIL import Image, ImageTk


NOTER_FOLDER = "noter"


class NoterTab:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)

        notebook = ttk.Notebook(self.frame)
        notebook.pack(fill="both", expand=True)

        if not os.path.exists(NOTER_FOLDER):
            os.makedirs(NOTER_FOLDER)

        for folder_name in sorted(os.listdir(NOTER_FOLDER)):
            folder_path = os.path.join(NOTER_FOLDER, folder_name)
            if os.path.isdir(folder_path):
                self._create_folder_tab(notebook, folder_name, folder_path)

    def _create_folder_tab(self, notebook, title, folder_path):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=title)

        # GRID LAYOUT
        tab.rowconfigure(0, weight=1)
        tab.columnconfigure(0, weight=0)   # sidebar
        tab.columnconfigure(1, weight=1)   # viewer

        # ---------- SIDEBAR ----------
        left_frame = ttk.Frame(tab, width=260)
        left_frame.grid(row=0, column=0, sticky="nsw")
        left_frame.grid_propagate(False)

        tk.Label(left_frame, text="Dokumenter", font=("Arial", 11, "bold"),
                 anchor="w").pack(fill="x", padx=10, pady=(10, 5))
        ttk.Separator(left_frame, orient="horizontal").pack(fill="x", padx=10)

        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)

        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical")
        tree_scroll.pack(side="right", fill="y")

        tree = ttk.Treeview(tree_frame, show="tree",
                            yscrollcommand=tree_scroll.set,
                            selectmode="browse")
        tree.pack(side="left", fill="both", expand=True)
        tree_scroll.config(command=tree.yview)

        # ---------- VIEWER ----------
        right_frame = ttk.Frame(tab)
        right_frame.grid(row=0, column=1, sticky="nsew")

        right_frame.rowconfigure(0, weight=1)
        right_frame.columnconfigure(0, weight=1)

        viewer_canvas = tk.Canvas(right_frame, bg="#f0f0f0")
        v_scroll = ttk.Scrollbar(right_frame, orient="vertical", command=viewer_canvas.yview)
        h_scroll = ttk.Scrollbar(right_frame, orient="horizontal", command=viewer_canvas.xview)

        viewer_canvas.configure(
            yscrollcommand=v_scroll.set,
            xscrollcommand=h_scroll.set
        )

        viewer_canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        status_var = tk.StringVar(value="Vælg et dokument til venstre")
        status_label = tk.Label(right_frame, textvariable=status_var,
                                font=("Arial", 9), fg="gray", anchor="w")
        status_label.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=(2, 4))

        # ---------- RESIZE GRIP ----------
        resize_grip = tk.Label(right_frame, cursor="size_nw_se", bg="#d0d0d0", width=2)
        resize_grip.grid(row=3, column=1, sticky="se")

        def start_resize(event):
            resize_grip.start_x = event.x_root
            resize_grip.start_y = event.y_root
            resize_grip.start_width = right_frame.winfo_width()
            resize_grip.start_height = right_frame.winfo_height()

        def do_resize(event):
            dx = event.x_root - resize_grip.start_x
            dy = event.y_root - resize_grip.start_y

            new_width = max(300, resize_grip.start_width + dx)
            new_height = max(300, resize_grip.start_height + dy)

            tab.grid_columnconfigure(1, minsize=new_width)
            tab.grid_rowconfigure(0, minsize=new_height)

        resize_grip.bind("<Button-1>", start_resize)
        resize_grip.bind("<B1-Motion>", do_resize)

        # ---------- STATE ----------
        state = {
            "photo_refs": [],
            "current_pdf_path": None,
            "current_pdf_name": None,
            "pdf_map": {},
            "resize_after_id": None,
            "zoom": 1.0
        }

        # Byg træ
        self._build_tree(tree, "", folder_path, state["pdf_map"])

        # ---------- ZOOM ----------
        def on_zoom(event, canvas=viewer_canvas, s=state):
            if event.delta > 0:
                s["zoom"] = min(3.0, s["zoom"] + 0.1)
            else:
                s["zoom"] = max(0.3, s["zoom"] - 0.1)

            status_var.set(f"Zoom: {int(s['zoom']*100)}%")

            if s["current_pdf_path"]:
                self._reload_pdf(canvas, status_var, s)

        viewer_canvas.bind("<Control-MouseWheel>", on_zoom)

        # Events
        viewer_canvas.bind(
            "<Configure>",
            lambda e, s=state, c=viewer_canvas, sv=status_var:
                self._on_viewer_resize(c, sv, s)
        )

        tree.bind(
            "<<TreeviewSelect>>",
            lambda e, t=tree, c=viewer_canvas, sv=status_var, s=state:
                self._on_tree_select(t, c, sv, s)
        )

        tree.bind("<Double-1>", lambda e, t=tree: self._on_tree_double_click(e, t))

    # ---------- TRÆ ----------
    def _build_tree(self, tree, parent_id, folder_path, pdf_map):
        entries = sorted(os.listdir(folder_path))

        folders = [e for e in entries if os.path.isdir(os.path.join(folder_path, e))]
        pdfs = [e for e in entries if e.lower().endswith(".pdf")]

        for folder_name in folders:
            sub_path = os.path.join(folder_path, folder_name)
            node_id = tree.insert(parent_id, "end",
                                  text=f"  📁 {folder_name}",
                                  open=False)
            self._build_tree(tree, node_id, sub_path, pdf_map)

        for pdf_name in pdfs:
            pdf_path = os.path.join(folder_path, pdf_name)
            display_name = pdf_name.replace(".pdf", "").replace("_", " ")
            item_id = tree.insert(parent_id, "end",
                                  text=f"  📄 {display_name}")
            pdf_map[item_id] = (pdf_path, display_name)

    # ---------- EVENTS ----------
    def _on_tree_select(self, tree, canvas, status_var, state):
        selected = tree.selection()
        if not selected:
            return

        item_id = selected[0]

        if item_id in state["pdf_map"]:
            pdf_path, display_name = state["pdf_map"][item_id]
            self._load_pdf(canvas, status_var, pdf_path, display_name, state)

    def _on_tree_double_click(self, event, tree):
        item_id = tree.identify_row(event.y)
        if not item_id:
            return
        if tree.get_children(item_id):
            is_open = tree.item(item_id, "open")
            tree.item(item_id, open=not is_open)

    def _on_viewer_resize(self, canvas, status_var, state):
        if state["current_pdf_path"] is None:
            return

        if state.get("resize_after_id"):
            try:
                canvas.after_cancel(state["resize_after_id"])
            except Exception:
                pass

        state["resize_after_id"] = canvas.after(
            200,
            lambda: self._reload_pdf(canvas, status_var, state)
        )

    def _reload_pdf(self, canvas, status_var, state):
        self._load_pdf(
            canvas,
            status_var,
            state["current_pdf_path"],
            state["current_pdf_name"],
            state
        )

    # ---------- PDF LOADING ----------
    def _load_pdf(self, canvas, status_var, pdf_path, display_name, state):
        state["current_pdf_path"] = pdf_path
        state["current_pdf_name"] = display_name

        canvas.delete("all")
        state["photo_refs"] = []

        status_var.set(f"Indlæser: {display_name}...")

        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            canvas.create_text(
                300, 150,
                text=f"Kunne ikke åbne PDF:\n{e}",
                font=("Arial", 11),
                fill="red"
            )
            status_var.set("Fejl ved indlæsning")
            return

        y_offset = 10
        page_gap = 15
        canvas_width = max(canvas.winfo_width(), 200)

        try:
            for page_num in range(len(doc)):
                page = doc[page_num]

                page_width = page.rect.width
                if page_width <= 0:
                    continue

                base_scale = (canvas_width - 20) / page_width
                scale = base_scale * state["zoom"]
                mat = fitz.Matrix(scale, scale)

                pix = page.get_pixmap(matrix=mat)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                photo = ImageTk.PhotoImage(img)

                state["photo_refs"].append(photo)

                canvas.create_image(10, y_offset, anchor="nw", image=photo)

                canvas.create_text(
                    10 + pix.width / 2,
                    y_offset + pix.height + 4,
                    text=f"Side {page_num + 1} / {len(doc)}",
                    font=("Arial", 8),
                    fill="gray"
                )

                y_offset += pix.height + page_gap
        except Exception as e:
            doc.close()
            canvas.create_text(
                300, 150,
                text=f"Fejl ved visning af PDF:\n{e}",
                font=("Arial", 11),
                fill="red"
            )
            status_var.set("Fejl ved indlæsning")
            return

        canvas.configure(scrollregion=(0, 0, canvas_width, y_offset))
        doc.close()

        status_var.set(f"{display_name}  —  {len(state['photo_refs'])} sider")

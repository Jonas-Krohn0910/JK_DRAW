class Netlist3Phase:
    def __init__(self):
        self.components = {}
        self.counter = {"R": 1, "L": 1, "C": 1, "Z":1}

    def add_component(self, ctype, n1, n2):
        name = f"{ctype}{self.counter[ctype]}"
        self.counter[ctype] += 1

        self.components[name] = {
            "name": name,
            "type": ctype,
            "value": 1.0,
            "angle": 0.0,
            "n1": n1,
            "n2": n2,
        
            "canvas_ids": []
        }
        return name

    def attach_canvas_ids(self, name, *ids):
        self.components[name]["canvas_ids"] = ids

    def delete_component(self, name, canvas):
        for cid in self.components[name]["canvas_ids"]:
            canvas.delete(cid)
        del self.components[name]

    def find_component_by_canvas_id(self, x, y, canvas):
        clicked = canvas.find_closest(x, y)
        cid = clicked[0]

        for name, comp in self.components.items():
            if cid in comp["canvas_ids"]:
                return name
        return None

    def rename_component(self, old, new):
        self.components[new] = self.components.pop(old)
        self.components[new]["name"] = new

    def redraw_all(self, canvas, node_y):
        for comp in self.components.values():
            n1 = comp["n1"]
            n2 = comp["n2"]
            y1 = node_y[n1]
            y2 = node_y[n2]
            x = 300

            box = canvas.create_rectangle(x - 20, (y1 + y2) / 2 - 10,
                                          x + 20, (y1 + y2) / 2 + 10,
                                          fill="lightgray")
            label = canvas.create_text(x, (y1 + y2) / 2, text=comp["name"])
            comp["canvas_ids"] = [box, label]

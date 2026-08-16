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

import numpy as np
import math


class ACSolver:
    def __init__(self, circuit_data):
        self.components = circuit_data["components"]
        self.frequency = circuit_data["frequency"]
        self.omega = 2 * math.pi * self.frequency

        # ---------------------------------------------------------
        # Find ALLE node-id'er der faktisk bruges (undtagen GND=0)
        # ---------------------------------------------------------
        used_nodes = set()
        for c in self.components:
            if c["n1"] != 0:
                used_nodes.add(c["n1"])
            if c["n2"] != 0:
                used_nodes.add(c["n2"])

        # Komprimer node-numre: fx {1,2,5} → {1,2,3}
        self.node_map = {}
        for new_index, old_node in enumerate(sorted(used_nodes)):
            self.node_map[old_node] = new_index

        self.N = len(self.node_map)

        # Spændingskilder
        self.voltage_sources = [c for c in self.components if c["type"] == "AC"]
        self.M = len(self.voltage_sources)

    def solve(self):
        N = self.N
        M = self.M
        omega = self.omega

        if N == 0:
            raise ValueError("Ingen noder i kredsløbet.")

        # MNA-matricer
        G = np.zeros((N, N), dtype=complex)
        B = np.zeros((N, M), dtype=complex)
        C = np.zeros((M, N), dtype=complex)
        D = np.zeros((M, M), dtype=complex)

        I = np.zeros(N, dtype=complex)
        E = np.zeros(M, dtype=complex)

        # ---------------------------------------------------------
        # 1) R, L, C → admittanser i G
        # ---------------------------------------------------------
        for c in self.components:
            t = c["type"]
            n1 = c["n1"]
            n2 = c["n2"]

            if t == "R":
                R = c["value"]
                if R == 0:
                    continue
                Y = 1.0 / R

            elif t == "L":
                L = c["value"]
                Z = 1j * omega * L
                if Z == 0:
                    continue
                Y = 1.0 / Z

            elif t == "C":
                Cval = c["value"]
                Y = 1j * omega * Cval

            else:
                continue

            if n1 != 0:
                i = self.node_map[n1]
                G[i, i] += Y
            if n2 != 0:
                j = self.node_map[n2]
                G[j, j] += Y
            if n1 != 0 and n2 != 0:
                i = self.node_map[n1]
                j = self.node_map[n2]
                G[i, j] -= Y
                G[j, i] -= Y

        # ---------------------------------------------------------
        # 2) Spændingskilder → B, C, E
        # ---------------------------------------------------------
        for k, src in enumerate(self.voltage_sources):
            n1 = src["n1"]
            n2 = src["n2"]
            Vsrc = src["voltage"]

            if n1 != 0:
                i = self.node_map[n1]
                B[i, k] = 1.0
                C[k, i] = 1.0
            if n2 != 0:
                j = self.node_map[n2]
                B[j, k] = -1.0
                C[k, j] = -1.0

            E[k] = Vsrc

        # ---------------------------------------------------------
        # 3) Saml MNA-system
        # ---------------------------------------------------------
        A = np.block([
            [G, B],
            [C, D]
        ])
        z = np.concatenate([I, E])

        # ---------------------------------------------------------
        # 4) Løs systemet
        # ---------------------------------------------------------
        try:
            x = np.linalg.solve(A, z)
        except np.linalg.LinAlgError as e:
            raise ValueError(f"Singular matrix i solver: {e}")

        V_nodes = x[:N]
        J_sources = x[N:]

        # ---------------------------------------------------------
        # 5) Node-spændinger (map tilbage til originale node-id'er)
        # ---------------------------------------------------------
        node_voltages = {0: 0+0j}
        for old_node, idx in self.node_map.items():
            node_voltages[old_node] = V_nodes[idx]

        # ---------------------------------------------------------
        # 6) Strøm gennem komponenter
        # ---------------------------------------------------------
        comp_currents = {}

        for c in self.components:
            t = c["type"]
            n1 = c["n1"]
            n2 = c["n2"]

            V1 = node_voltages[n1]
            V2 = node_voltages[n2]

            if t == "R":
                R = c["value"]
                Icomp = (V1 - V2) / R

            elif t == "L":
                L = c["value"]
                Z = 1j * omega * L
                Icomp = (V1 - V2) / Z

            elif t == "C":
                Cval = c["value"]
                Z = 1.0 / (1j * omega * Cval)
                Icomp = (V1 - V2) / Z

            elif t == "AC":
                idx = None
                for k, src in enumerate(self.voltage_sources):
                    if src["name"] == c["name"]:
                        idx = k
                        break
                Icomp = J_sources[idx] if idx is not None else 0

            comp_currents[c["name"]] = Icomp

        # ---------------------------------------------------------
        # 7) Spænding over komponenter
        # ---------------------------------------------------------
        comp_voltages = {}
        for c in self.components:
            V1 = node_voltages[c["n1"]]
            V2 = node_voltages[c["n2"]]
            comp_voltages[c["name"]] = V1 - V2

        # ---------------------------------------------------------
        # 8) Total impedans (hvis én AC-kilde)
        # ---------------------------------------------------------
        Ztotal = None
        Itotal = None

        if len(self.voltage_sources) == 1:
            src = self.voltage_sources[0]
            Vsrc = src["voltage"]
            Itotal = comp_currents[src["name"]]
            if Itotal != 0:
                Ztotal = Vsrc / Itotal

        return {
            "node_voltages": node_voltages,
            "component_currents": comp_currents,
            "component_voltages": comp_voltages,
            "total_impedance": Ztotal,
            "total_current": Itotal
        }

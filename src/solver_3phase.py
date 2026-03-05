import math
import cmath


def solve_3phase(netlist, phases):
    """
    netlist: Netlist3Phase-objekt
    phases: dict med noder -> {"V": kompleks spænding, "f": frekvens}
            kendte spændingsnoder: typisk "L1", "L2", "L3", "N"
    Returnerer:
        {
            "I": {"L1": I_L1, "L2": I_L2, "L3": I_L3, "N": I_N},
            "S": {"L1": S1, "L2": S2, "L3": S3},
            "cosphi": {"L1": cosφ1, "L2": cosφ2, "L3": cosφ3}
        }
    """

    # -------------------------------------------------
    # 1) Find alle noder i netlisten
    # -------------------------------------------------
    all_nodes = set()

    for comp in netlist.components.values():
        all_nodes.add(comp["n1"])
        all_nodes.add(comp["n2"])

    # kendte spændingsnoder
    known_nodes = set(phases.keys())

    # ukendte noder (skal løses)
    unknown_nodes = list(all_nodes - known_nodes)

    # hvis ingen ukendte noder → gammel metode virker
    if not unknown_nodes:
        I_node = {n: 0 + 0j for n in phases.keys()}

        for comp in netlist.components.values():
            ctype = comp["type"]
            n1 = comp["n1"]
            n2 = comp["n2"]
            val = float(comp["value"])
            angle_deg = float(comp.get("angle", 0.0))

            f = phases.get(n1, phases["L1"])["f"]
            w = 2 * math.pi * f

            if ctype == "R":
                Z = val
            elif ctype == "L":
                # mH -> H
                L_H = val / 1000.0
                Z = 1j * w * L_H
            elif ctype == "C":
                # µF -> F
                if val == 0:
                    continue
                C_F = val * 1e-6
                Z = 1 / (1j * w * C_F)
            elif ctype == "Z":
                # Generel impedans: |Z| og fasevinkel (grader)
                Z = cmath.rect(val, math.radians(angle_deg))
            else:
                continue

            if Z == 0:
                continue

            V1 = phases[n1]["V"]
            V2 = phases[n2]["V"]

            I = (V1 - V2) / Z

            I_node[n1] += I
            I_node[n2] -= I

        I_phase = {
            "L1": I_node.get("L1", 0 + 0j),
            "L2": I_node.get("L2", 0 + 0j),
            "L3": I_node.get("L3", 0 + 0j),
            "N": I_node.get("N", 0 + 0j),
        }

    else:
        # -------------------------------------------------
        # 2) Opbyg Y-matrix (admittansmatrix)
        # -------------------------------------------------
        N = len(unknown_nodes)
        Y = [[0 + 0j for _ in range(N)] for _ in range(N)]
        I_inj = [0 + 0j for _ in range(N)]

        node_index = {node: i for i, node in enumerate(unknown_nodes)}

        for comp in netlist.components.values():
            ctype = comp["type"]
            n1 = comp["n1"]
            n2 = comp["n2"]
            val = float(comp["value"])
            angle_deg = float(comp.get("angle", 0.0))

            f = phases.get(n1, phases["L1"])["f"]
            w = 2 * math.pi * f

            if ctype == "R":
                Z = val
            elif ctype == "L":
                L_H = val / 1000.0
                Z = 1j * w * L_H
            elif ctype == "C":
                if val == 0:
                    continue
                C_F = val * 1e-6
                Z = 1 / (1j * w * C_F)
            elif ctype == "Z":
                Z = cmath.rect(val, math.radians(angle_deg))
            else:
                continue

            if Z == 0:
                continue

            Y_branch = 1 / Z

            for (a, b, sign) in [(n1, n2, 1), (n2, n1, 1)]:
                if a in unknown_nodes:
                    i = node_index[a]

                    Y[i][i] += Y_branch

                    if b in unknown_nodes:
                        j = node_index[b]
                        Y[i][j] -= Y_branch
                    else:
                        Vb = phases[b]["V"]
                        I_inj[i] += Y_branch * Vb

        # -------------------------------------------------
        # 3) Løs lineært ligningssystem YV = I
        # -------------------------------------------------
        import numpy as np

        Y_np = np.array(Y, dtype=complex)
        I_np = np.array(I_inj, dtype=complex)

        V_unknown = np.linalg.solve(Y_np, I_np)

        # samle alle node-spændinger
        node_voltage = {}

        for n in phases:
            node_voltage[n] = phases[n]["V"]

        for i, n in enumerate(unknown_nodes):
            node_voltage[n] = V_unknown[i]

        # -------------------------------------------------
        # 4) Beregn strømme
        # -------------------------------------------------
        I_node = {n: 0 + 0j for n in node_voltage.keys()}

        for comp in netlist.components.values():
            ctype = comp["type"]
            n1 = comp["n1"]
            n2 = comp["n2"]
            val = float(comp["value"])
            angle_deg = float(comp.get("angle", 0.0))

            f = phases.get(n1, phases["L1"])["f"]
            w = 2 * math.pi * f

            if ctype == "R":
                Z = val
            elif ctype == "L":
                L_H = val / 1000.0
                Z = 1j * w * L_H
            elif ctype == "C":
                if val == 0:
                    continue
                C_F = val * 1e-6
                Z = 1 / (1j * w * C_F)
            elif ctype == "Z":
                Z = cmath.rect(val, math.radians(angle_deg))
            else:
                continue

            if Z == 0:
                continue

            V1 = node_voltage[n1]
            V2 = node_voltage[n2]

            I = (V1 - V2) / Z

            I_node[n1] += I
            I_node[n2] -= I

        I_phase = {
            "L1": I_node.get("L1", 0 + 0j),
            "L2": I_node.get("L2", 0 + 0j),
            "L3": I_node.get("L3", 0 + 0j),
            "N": I_node.get("N", 0 + 0j),
        }

    # -------------------------------------------------
    # 5) Effekt pr. fase
    # -------------------------------------------------
    S_phase = {}
    cosphi = {}

    for ph in ("L1", "L2", "L3"):
        if ph in phases:
            V = phases[ph]["V"]
            I = I_phase[ph]
            S = V * I.conjugate()
            S_phase[ph] = S

            if abs(S) > 0:
                cosphi[ph] = S.real / abs(S)
            else:
                cosphi[ph] = 1.0
        else:
            S_phase[ph] = 0 + 0j
            cosphi[ph] = 1.0

    return {
        "I": I_phase,
        "S": S_phase,
        "cosphi": cosphi,
    }

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

        node_voltage = {n: phases[n]["V"] for n in phases}

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

    steps = build_calculation_steps(netlist, phases, node_voltage, I_phase, S_phase, cosphi)

    return {
        "I": I_phase,
        "S": S_phase,
        "cosphi": cosphi,
        "steps": steps,
    }


def _fmt_polar(z, unit=""):
    """Formaterer et komplekst tal som 'størrelse @ vinkel°', uden tegn
    (∠, ω, φ, π) der ikke gengives korrekt af PDF-eksportens standardfont."""
    mag = abs(z)
    ang = math.degrees(cmath.phase(z))
    suffix = f" {unit}" if unit else ""
    return f"{mag:.4f} @ {ang:.2f}°{suffix}"


def build_calculation_steps(netlist, phases, node_voltage, I_phase, S_phase, cosphi):
    """Bygger en styled, læsbar gennemgang af hele 3-faset beregningen,
    til brug i PDF-eksporten af mellemregninger.

    Returnerer en liste af {"style": ..., "text": ...} i stedet for flad
    tekst, så PDF-eksporten kan give den visuel hierarki (titel/sektion/
    komponent/resultat) - en ren tekst-væg viste sig uoverskuelig for
    brugeren i praksis.
    """
    steps = []

    def add(style, text=""):
        steps.append({"style": style, "text": text})

    type_names = {"R": "Modstand", "L": "Spole", "C": "Kondensator", "Z": "Impedans"}

    # ---------------------------------------------------------
    # Resultat-overblik - svaret først, så man ikke skal lede efter det
    # ---------------------------------------------------------
    add("title", "3-faset AC-beregning")
    add("section", "RESULTAT-OVERBLIK")

    add("table_header", f"{'Fase':<6}{'Stroem (I)':<24}{'S (VA)':>10}{'P (W)':>11}{'Q (var)':>11}{'cos(phi)':>11}")
    for ph in ("L1", "L2", "L3"):
        I = I_phase[ph]
        S = S_phase[ph]
        add(
            "result",
            f"{ph:<6}{_fmt_polar(I):<24}{abs(S):>10.1f}{S.real:>11.1f}{S.imag:>11.1f}{cosphi[ph]:>11.4f}",
        )
    add("body", f"{'N':<6}{_fmt_polar(I_phase['N'], 'A')}  (nulleder-stroem)")
    add("spacer")

    add("body", "Linjespaendinger:")
    for a, b in (("L1", "L2"), ("L2", "L3"), ("L3", "L1")):
        Vline = phases[a]["V"] - phases[b]["V"]
        add("result", f"  U_{a}{b} = {_fmt_polar(Vline, 'V')}")
    add("spacer")
    add("body", "Se de fulde mellemregninger for hvert trin herunder.")
    add("spacer")

    # ---------------------------------------------------------
    # Kildespændinger
    # ---------------------------------------------------------
    add("section", "KILDESPAENDINGER OG FREKVENS")
    for node in ("L1", "L2", "L3"):
        V = phases[node]["V"]
        f = phases[node]["f"]
        add("body", f"  U_{node} = {_fmt_polar(V, 'V')}   (f = {f:.3f} Hz)")
    add("body", f"  U_N  = {_fmt_polar(phases['N']['V'], 'V')}  (nulpunkt)")
    add("spacer")

    # ---------------------------------------------------------
    # Interne knudepunkter (kun hvis relevant)
    # ---------------------------------------------------------
    extra_nodes = [n for n in node_voltage if n not in ("L1", "L2", "L3", "N")]
    if extra_nodes:
        add("section", "LOESTE KNUDESPAENDINGER (interne knudepunkter)")
        add("body", "  Fundet ved at loese admittansmatrix-ligningen Y*V = I")
        for n in extra_nodes:
            add("result", f"  U_{n} = {_fmt_polar(node_voltage[n], 'V')}")
        add("spacer")

    # ---------------------------------------------------------
    # Komponent-for-komponent
    # ---------------------------------------------------------
    add("section", "KOMPONENTBEREGNINGER")

    for name, comp in netlist.components.items():
        ctype = comp["type"]
        n1, n2 = comp["n1"], comp["n2"]
        val = float(comp["value"])
        angle_deg = float(comp.get("angle", 0.0))

        f = phases.get(n1, phases["L1"])["f"]
        w = 2 * math.pi * f

        add("component", f"{name} - {type_names.get(ctype, ctype)} (mellem {n1} og {n2})")

        if ctype == "R":
            Z = val
            add("body", f"  Z = R = {val:.4f} Ohm  ->  {_fmt_polar(Z, 'Ohm')}")
        elif ctype == "L":
            L_H = val / 1000.0
            Z = 1j * w * L_H
            add("body", f"  L = {val:.4f} mH = {L_H:.6f} H,  w = 2*pi*{f:.3f} = {w:.4f} rad/s")
            add("body", f"  Z = j*w*L = {_fmt_polar(Z, 'Ohm')}")
        elif ctype == "C":
            if val == 0:
                add("body", "  C = 0 µF -> springes over (uendelig impedans)")
                add("spacer")
                continue
            C_F = val * 1e-6
            Z = 1 / (1j * w * C_F)
            add("body", f"  C = {val:.4f} µF = {C_F:.9f} F,  w = 2*pi*{f:.3f} = {w:.4f} rad/s")
            add("body", f"  Z = 1/(j*w*C) = {_fmt_polar(Z, 'Ohm')}")
        elif ctype == "Z":
            Z = cmath.rect(val, math.radians(angle_deg))
            add("body", f"  |Z| = {val:.4f} Ohm,  vinkel = {angle_deg:.2f}°")
            add("body", f"  Z = {_fmt_polar(Z, 'Ohm')}")
        else:
            add("body", "  Ukendt komponenttype - springes over")
            add("spacer")
            continue

        if Z == 0:
            add("body", "  Z = 0 -> springes over (kortslutning)")
            add("spacer")
            continue

        V1 = node_voltage.get(n1, 0 + 0j)
        V2 = node_voltage.get(n2, 0 + 0j)
        I = (V1 - V2) / Z

        add("body", f"  U_{n1} = {_fmt_polar(V1, 'V')},  U_{n2} = {_fmt_polar(V2, 'V')}")
        add("result", f"  I = (U_{n1} - U_{n2}) / Z = {_fmt_polar(I, 'A')}")
        add("spacer")

    # ---------------------------------------------------------
    # Sammenfatning + effekt (fuld udregning, ikke kun facit)
    # ---------------------------------------------------------
    add("section", "SAMMENFATTEDE FASESTROEMME")
    add("body", "  (sum af gren-stroemme ind/ud af hver knude)")
    for ph in ("L1", "L2", "L3", "N"):
        add("result", f"  I_{ph} = {_fmt_polar(I_phase[ph], 'A')}")
    add("spacer")

    add("section", "EFFEKT PR. FASE (S = U * I*)")
    for ph in ("L1", "L2", "L3"):
        V = phases[ph]["V"]
        I = I_phase[ph]
        S = S_phase[ph]
        add("component", ph)
        add("body", f"  S = U_{ph} * I_{ph}* = {_fmt_polar(V, 'V')} * conj({_fmt_polar(I, 'A')})")
        add(
            "result",
            f"  S = {abs(S):.4f} VA,  P = {S.real:.4f} W,  Q = {S.imag:.4f} var,  cos(phi) = {cosphi[ph]:.4f}",
        )
    add("spacer")

    add("section", "LINJESPAENDINGER")
    for a, b in (("L1", "L2"), ("L2", "L3"), ("L3", "L1")):
        Vline = phases[a]["V"] - phases[b]["V"]
        add("body", f"  U_{a}{b} = U_{a} - U_{b}")
        add("result", f"  U_{a}{b} = {_fmt_polar(Vline, 'V')}")

    return steps

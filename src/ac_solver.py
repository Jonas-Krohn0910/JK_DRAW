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

            elif t == "Z":
                Z = c["value"]
                if Z == 0:
                    continue
                Y = 1.0 / Z
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
                Icomp = (V1 - V2) / R if R != 0 else 0 + 0j

            elif t == "L":
                L = c["value"]
                Z = 1j * omega * L
                Icomp = (V1 - V2) / Z if Z != 0 else 0 + 0j

            elif t == "C":
                Cval = c["value"]
                if Cval == 0:
                    Icomp = 0 + 0j
                else:
                    Z = 1.0 / (1j * omega * Cval)
                    Icomp = (V1 - V2) / Z

            elif t == "Z":
                Z = c["value"]
                Icomp = (V1 - V2) / Z if Z != 0 else 0 + 0j

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

            idx = 0  # kun én kilde
            Itotal = J_sources[idx]   # brug MNA-strøm direkte

            if Itotal != 0:
                Ztotal = -Vsrc / Itotal

        steps = build_calculation_steps(
            self.components, self.frequency, node_voltages,
            comp_currents, comp_voltages, Ztotal, Itotal
        )

        return {
            "node_voltages": node_voltages,
            "component_currents": comp_currents,
            "component_voltages": comp_voltages,
            "total_impedance": Ztotal,
            "total_current": Itotal,
            "steps": steps
        }


def _fmt_polar(z, unit=""):
    """Formaterer et komplekst tal som 'størrelse @ vinkel°', uden tegn
    (∠, ω, φ, π) der ikke gengives korrekt af PDF-eksportens standardfont."""
    mag = abs(z)
    ang = math.degrees(math.atan2(z.imag, z.real))
    suffix = f" {unit}" if unit else ""
    return f"{mag:.4f} @ {ang:.2f}°{suffix}"


def _impedance_character(z):
    """Bestemmer om en impedans er induktiv, kapacitiv eller rent resistiv
    ud fra fortegnet på vinklen (positiv = induktiv, negativ = kapacitiv)."""
    ang = math.degrees(math.atan2(z.imag, z.real))
    if ang > 1e-9:
        return ang, "induktiv"
    if ang < -1e-9:
        return ang, "kapacitiv"
    return ang, "rent resistiv"


def build_calculation_steps(components, frequency, node_voltages, comp_currents,
                             comp_voltages, Ztotal, Itotal):
    """Bygger en styled, læsbar gennemgang af 1-faset AC-beregningen,
    til brug i PDF-eksporten af mellemregninger (se solver_3phase.py for
    den tilsvarende 3-fasede udgave)."""
    steps = []

    def add(style, text=""):
        steps.append({"style": style, "text": text})

    type_names = {"R": "Modstand", "L": "Spole", "C": "Kondensator",
                  "Z": "Impedans", "AC": "Spændingskilde"}

    # ---------------------------------------------------------
    # Samlet effekt leveret af AC-kilde(rne). Bruger den fysiske
    # udgangsstroem (-comp_currents[navn]), da comp_currents for en
    # spaendingskilde er MNA-grenstroemmen der pr. konvention regnes IND
    # i kilden (modsat fortegn af den fysiske stroem der loeber ud i
    # kredsloebet - se noten ved Z_total nedenfor).
    # ---------------------------------------------------------
    S_total = 0 + 0j
    for c in components:
        if c["type"] != "AC":
            continue
        name = c["name"]
        Vc = comp_voltages.get(name, 0 + 0j)
        I_out = -comp_currents.get(name, 0 + 0j)
        S_total += Vc * I_out.conjugate()

    P_total = S_total.real
    Q_total = S_total.imag
    S_mag = abs(S_total)
    cosphi_total = P_total / S_mag if S_mag > 0 else 1.0

    # ---------------------------------------------------------
    # Resultat-overblik - svaret først
    # ---------------------------------------------------------
    add("title", "1-faset AC-beregning")
    add("section", "RESULTAT-OVERBLIK")

    add("table_header", f"{'Komponent':<10}{'Stroem (I)':<24}{'Spaending (U)':<24}")
    for c in components:
        name = c["name"]
        I = comp_currents.get(name, 0 + 0j)
        V = comp_voltages.get(name, 0 + 0j)
        add("result", f"{name:<10}{_fmt_polar(I, 'A'):<24}{_fmt_polar(V, 'V'):<24}")
    add("spacer")

    if Ztotal is not None:
        ang_z, karakter_z = _impedance_character(Ztotal)
        add("result", f"  Z_total = {abs(Ztotal):.4f} Ohm @ {ang_z:+.2f}° ({karakter_z})")
        if karakter_z == "induktiv":
            add("body", "  -> Induktiv karakter: positiv vinkel, stroemmen efteriler spaendingen.")
        elif karakter_z == "kapacitiv":
            add("body", "  -> Kapacitiv karakter: negativ vinkel, stroemmen forudiler spaendingen.")
        else:
            add("body", "  -> Rent resistiv karakter: stroem og spaending er i fase.")
    if Itotal is not None:
        add("result", f"  I_total = {_fmt_polar(Itotal, 'A')}")
    add("spacer")
    add("result", f"  P (aktiv effekt)        = {P_total:.4f} W")
    add("result", f"  Q (reaktiv effekt)      = {Q_total:.4f} VAr")
    add("result", f"  S (tilsyneladende eff.) = {S_mag:.4f} VA")
    add("result", f"  cos(phi) (effektfaktor) = {cosphi_total:.4f}")
    add("spacer")
    add("body", "Se de fulde mellemregninger for hvert trin herunder.")
    add("spacer")

    # ---------------------------------------------------------
    # Kildespænding(er)
    # ---------------------------------------------------------
    add("section", "KILDESPAENDING OG FREKVENS")
    for c in components:
        if c["type"] != "AC":
            continue
        Vraw = c.get("voltage_raw", c["voltage"])
        fraw = c.get("frequency_raw", c["frequency"])
        add("body", f"  {c['name']}: U = {Vraw:.4f} V  (f = {fraw:.3f} Hz)")
    add("spacer")

    # ---------------------------------------------------------
    # Løste knudespændinger
    # ---------------------------------------------------------
    add("section", "KNUDESPAENDINGER")
    add("body", "  Fundet ved at loese MNA-ligningssystemet")
    for node in sorted(node_voltages.keys()):
        label = "GND (0)" if node == 0 else f"Knude {node}"
        add("result", f"  U_{label} = {_fmt_polar(node_voltages[node], 'V')}")
    add("spacer")

    # ---------------------------------------------------------
    # Komponent-for-komponent
    # ---------------------------------------------------------
    add("section", "KOMPONENTBEREGNINGER")
    omega = 2 * math.pi * frequency
    unit_check_shown = False
    fallback_unit_check = None  # (navn, Z, I) fra foerste R/Z-komponent, hvis intet L/C findes

    for c in components:
        ctype = c["type"]
        if ctype == "AC":
            continue

        name = c["name"]
        n1, n2 = c["n1"], c["n2"]
        add("component", f"{name} - {type_names.get(ctype, ctype)} (mellem knude {n1} og {n2})")

        if ctype == "R":
            Rraw = c.get("value_raw", c["value"])
            Z = c["value"]
            add("body", f"  Z = R = {Rraw:.4f} Ohm")

        elif ctype == "L":
            Lraw = c.get("value_raw", 0.0)
            L_H = c["value"]
            Z = 1j * omega * L_H
            add("body", f"  L = {Lraw:.4f} mH = {L_H:.6f} H,  w = 2*pi*{frequency:.3f} = {omega:.4f} rad/s")
            add("body", f"  Z = j*w*L = {_fmt_polar(Z, 'Ohm')}")
            if not unit_check_shown:
                add("body", "  Enhedscheck: [w][L] = (rad/s)*(H) = (1/s)*(V*s/A) = V/A = Ohm  (rad er enhedsloes) OK")
                unit_check_shown = True

        elif ctype == "C":
            Craw = c.get("value_raw", 0.0)
            C_F = c["value"]
            if C_F == 0:
                add("body", "  C = 0 µF -> springes over (uendelig impedans)")
                add("spacer")
                continue
            Z = 1 / (1j * omega * C_F)
            add("body", f"  C = {Craw:.4f} µF = {C_F:.9f} F,  w = 2*pi*{frequency:.3f} = {omega:.4f} rad/s")
            add("body", f"  Z = 1/(j*w*C) = {_fmt_polar(Z, 'Ohm')}")
            if not unit_check_shown:
                add("body", "  Enhedscheck: 1/([w][C]) = 1/((1/s)*(A*s/V)) = V/A = Ohm  (rad er enhedsloes) OK")
                unit_check_shown = True

        elif ctype == "Z":
            Rraw = c.get("R_raw", 0.0)
            phiraw = c.get("phi_raw", 0.0)
            Z = c["value"]
            add("body", f"  |Z| = {Rraw:.4f} Ohm,  vinkel = {phiraw:.2f}°")
            add("body", f"  Z = {_fmt_polar(Z, 'Ohm')}")

        else:
            add("body", "  Ukendt komponenttype - springes over")
            add("spacer")
            continue

        if Z == 0:
            add("body", "  Z = 0 -> springes over (kortslutning)")
            add("spacer")
            continue

        V1 = node_voltages.get(n1, 0 + 0j)
        V2 = node_voltages.get(n2, 0 + 0j)
        I = comp_currents.get(name, 0 + 0j)

        add("body", f"  U_{n1} = {_fmt_polar(V1, 'V')},  U_{n2} = {_fmt_polar(V2, 'V')}")
        add("result", f"  I = (U_{n1} - U_{n2}) / Z = {_fmt_polar(I, 'A')}")
        if ctype in ("R", "Z") and fallback_unit_check is None:
            fallback_unit_check = (name, Z, I)
        add("spacer")

    # Fald tilbage til et Ohms lov-eksempel hvis kredsloebet ikke har L/C
    # (deres j*w*L / 1/(j*w*C)-udtryk giver et mere illustrativt enhedscheck).
    if not unit_check_shown and fallback_unit_check is not None:
        fb_name, fb_Z, fb_I = fallback_unit_check
        add("body", f"  Enhedscheck (jf. {fb_name}): [U]/[Z] = V/Ohm = A  ->  {_fmt_polar(fb_I, 'A')} OK")
        unit_check_shown = True

    # ---------------------------------------------------------
    # Total impedans og strøm
    # ---------------------------------------------------------
    add("section", "TOTAL IMPEDANS OG STROEM")
    if Ztotal is not None and Itotal is not None:
        add("body", "  Kun beregnet naar kredsloebet har praecis 1 spaendingskilde.")
        add("body", "  Z_total = -U_kilde / I_total")
        add("body", "  Bemaerk: minustegnet er IKKE en fejl. I_total er defineret efter MNA/KVL-")
        add("body", "  konventionen som den grenstroem der floeder IND i spaendingskilden. Den")
        add("body", "  fysiske stroem der loeber UD i det ydre kredsloeb er derfor -I_total.")
        add("result", f"  Z_total = {_fmt_polar(Ztotal, 'Ohm')}")
        add("result", f"  I_total = {_fmt_polar(Itotal, 'A')}")
    else:
        add("body", "  Ikke beregnet (kraever praecis 1 AC-kilde i kredsloebet).")
    add("spacer")

    # ---------------------------------------------------------
    # Effektberegning
    # ---------------------------------------------------------
    add("section", "EFFEKTBEREGNING")
    for c in components:
        if c["type"] != "AC":
            continue
        name = c["name"]
        Vc = comp_voltages.get(name, 0 + 0j)
        I_out = -comp_currents.get(name, 0 + 0j)
        Sc = Vc * I_out.conjugate()
        add("component", f"{name} (kildens leverede effekt)")
        add("body", f"  I_ud = -I_{name} = {_fmt_polar(I_out, 'A')}  (fysisk udgangsstroem, se note ovenfor)")
        add("body", f"  S = U_{name} * conj(I_ud) = {_fmt_polar(Vc, 'V')} * conj({_fmt_polar(I_out, 'A')})")
        add("result", f"  S = {abs(Sc):.4f} VA,  P = {Sc.real:.4f} W,  Q = {Sc.imag:.4f} VAr")
        add("spacer")

    add("body", "Summeret over alle kilder:")
    add("result", f"  Aktiv effekt        P = {P_total:.4f} W")
    add("result", f"  Reaktiv effekt      Q = {Q_total:.4f} VAr")
    add("result", f"  Tilsyneladende eff. S = {S_mag:.4f} VA")
    add("result", f"  Effektfaktor  cos(phi) = {cosphi_total:.4f}")

    return steps

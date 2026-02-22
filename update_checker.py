import requests
import zipfile
import io
import os
import shutil
import tkinter.messagebox as mb
import subprocess 
import sys

# JK_DRAW - Engineering Visualization Tool
# Author: Jonas
# License: MIT

UPDATE_URL_VERSION = "https://raw.githubusercontent.com/Jonas-Krohn0910/JK_DRAW/main/version.txt"
UPDATE_URL_ZIP = "https://github.com/Jonas-Krohn0910/JK_DRAW/archive/refs/heads/main.zip"

LOCAL_VERSION_FILE = "version.txt"


# ---------------------------------------------------------
# MAPPEROOT
# ---------------------------------------------------------

def get_project_root():
    """Returnerer projektroden (mappen hvor updater_checker.py ligger)."""
    return os.path.dirname(os.path.abspath(__file__))


def get_src_root():
    """Returnerer src-mappen inde i projektroden."""
    return os.path.join(get_project_root(), "src")


# ---------------------------------------------------------
# VERSIONHÅNDTERING
# ---------------------------------------------------------

def get_local_version():
    path = os.path.join(get_project_root(), LOCAL_VERSION_FILE)

    if not os.path.exists(path):
        print("[DEBUG] Lokal version.txt blev ikke fundet. Bruger 0.0.0")
        return "0.0.0"

    try:
        with open(path, "r", encoding="utf-8") as f:
            version = f.read().strip()
            if version == "":
                print("[DEBUG] Lokal version.txt er tom. Bruger 0.0.0")
                return "0.0.0"

            print(f"[DEBUG] Lokal version fundet: {version}")
            return version

    except Exception as e:
        print(f"[FEJL] Ved læsning af lokal version.txt: {e}")
        return "0.0.0"


def get_online_version():
    try:
        print(f"[DEBUG] Henter online version fra: {UPDATE_URL_VERSION}")
        r = requests.get(UPDATE_URL_VERSION, timeout=5)
        r.raise_for_status()
        online_version = r.text.strip()
        print(f"[DEBUG] Online version hentet: {online_version}")
        return online_version
    except Exception as e:
        print(f"[FEJL] Kunne ikke hente online version: {e}")
        return None


def version_tuple(v):
    try:
        return tuple(map(int, v.split(".")))
    except:
        print(f"[FEJL] Ugyldigt versionsformat: {v}")
        return (0, 0, 0)


def update_available(local, online):
    lv = version_tuple(local)
    ov = version_tuple(online)
    print(f"[DEBUG] Sammenligner versioner: lokal={lv}, online={ov}")
    return ov > lv


# ---------------------------------------------------------
# DOWNLOAD & UDPAKNING (KORREKT VERSION)
# ---------------------------------------------------------

def download_and_extract_zip():
    try:
        print(f"[DEBUG] Downloader ZIP fra: {UPDATE_URL_ZIP}")
        r = requests.get(UPDATE_URL_ZIP, timeout=10)
        r.raise_for_status()

        # Midlertidig mappe
        temp_dir = os.path.join(get_project_root(), "_update_temp")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)

        print(f"[DEBUG] Udpakker ZIP midlertidigt i: {temp_dir}")
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(temp_dir)

        # GitHub laver altid én undermappe, fx JK_DRAW-main
        extracted_root = os.path.join(temp_dir, os.listdir(temp_dir)[0])
        print(f"[DEBUG] Filer fundet i: {extracted_root}")

        src_root = get_src_root()

        # Kopiér ALLE filer fra extracted_root/src → src/
        new_src = os.path.join(extracted_root, "src")

        if not os.path.exists(new_src):
            print("[FEJL] ZIP indeholder ikke en src-mappe!")
            return False

        print("[DEBUG] Opdaterer src-mappen...")

        for item in os.listdir(new_src):
            s = os.path.join(new_src, item)
            d = os.path.join(src_root, item)

            # Undgå at slette updater_checker.py
            if item == "updater_checker.py":
                continue

            if os.path.isdir(s):
                if os.path.exists(d):
                    shutil.rmtree(d)
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

        print("[DEBUG] src/ opdateret korrekt")

        # Opdater filer i projektroden (fx version.txt)
        for item in os.listdir(extracted_root):
            if item == "src":
                continue

            s = os.path.join(extracted_root, item)
            d = os.path.join(get_project_root(), item)

            if os.path.isdir(s):
                if os.path.exists(d):
                    shutil.rmtree(d)
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

        print("[DEBUG] Projektrod opdateret korrekt")

        # Ryd op
        shutil.rmtree(temp_dir)
        print("[DEBUG] Midlertidige filer slettet")

        return True

    except Exception as e:
        print(f"[FEJL] Kunne ikke downloade eller udpakke ZIP: {e}")
        return False


# ---------------------------------------------------------
# HOVEDFUNKTION
# ---------------------------------------------------------

def check_for_updates(show_popup=False):
    print("=== Starter opdaterings-tjek ===")

    local = get_local_version()
    online = get_online_version()

    if online is None:
        print("[INFO] Ingen online version tilgængelig.")
        if show_popup:
            mb.showerror("Ingen internetforbindelse",
                         "Kunne ikke kontakte opdateringsserveren.")
        return

    if update_available(local, online):
        print(f"[INFO] Ny version fundet: {online} (lokal: {local})")

        if show_popup:
            if not mb.askyesno("Opdatering fundet",
                               f"Ny version {online} er tilgængelig.\nVil du opdatere nu?"):
                print("[INFO] Brugeren afviste opdatering.")
                return

        if download_and_extract_zip():
            try:
                version_path = os.path.join(get_project_root(), LOCAL_VERSION_FILE)
                with open(version_path, "w", encoding="utf-8") as f:
                    f.write(online)
                print(f"[INFO] Lokal version.txt opdateret til: {online}")
            except Exception as e:
                print(f"[FEJL] Kunne ikke skrive version.txt: {e}")

            if show_popup:
                mb.showinfo("Opdatering", f"Programmet er opdateret til {online}.")
                # Tilbyd genstart
                if mb.askyesno("Genstart", "Programmet er opdateret.\nVil du genstarte nu?"):
                    python_exe = sys.executable
                    script_path = os.path.join(get_src_root(), "main.py")
                    subprocess.Popen([python_exe, script_path])
                    os._exit(0)

        else:
            print("[FEJL] Opdateringen mislykkedes.")
            if show_popup:
                mb.showerror("Fejl", "Opdateringen kunne ikke installeres.")
    else:
        print(f"[INFO] Ingen opdatering nødvendig. Lokal version: {local}")
        if show_popup:
            mb.showinfo("Ajour", f"Du bruger den nyeste version ({local}).")


if __name__ == "__main__":
    check_for_updates(show_popup=False)

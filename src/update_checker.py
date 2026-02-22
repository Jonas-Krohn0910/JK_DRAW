import requests
import zipfile
import io
import os
import tkinter.messagebox as mb
# JK_DRAW - Engineering Visualization Tool
# Author: Jonas <efternavn hvis du vil>
# Created: 2024
# License: MIT

UPDATE_URL_VERSION = "http://www.wosylus.com/test/version%202.txt"
UPDATE_URL_ZIP = "http://www.wosylus.com/test/JK_draw%202.zip"

LOCAL_VERSION_FILE = "version.txt"


# ---------------------------------------------------------
# MAPPEROOT
# ---------------------------------------------------------

def get_src_root():
    """Returnerer mappen hvor updater.py ligger (src/)."""
    return os.path.dirname(os.path.abspath(__file__))


def get_project_root():
    """Returnerer projektroden (mappen over src/)."""
    return os.path.dirname(get_src_root())


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
# DOWNLOAD & UDPAKNING
# ---------------------------------------------------------

def download_and_extract_zip():
    try:
        print(f"[DEBUG] Downloader ZIP fra: {UPDATE_URL_ZIP}")
        r = requests.get(UPDATE_URL_ZIP, timeout=10)
        r.raise_for_status()

        z = zipfile.ZipFile(io.BytesIO(r.content))

        extract_path = get_project_root()
        print(f"[DEBUG] Udpakker ZIP til projektrod: {extract_path}")

        z.extractall(extract_path)

        print("[DEBUG] ZIP udpakket uden fejl")
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

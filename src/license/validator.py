import base64
import json
import os
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization

from .hardware import get_hardware_id
from .public_key import PUBLIC_KEY_PEM

_PUBLIC_KEY = serialization.load_pem_public_key(PUBLIC_KEY_PEM)


def get_license_path():
    """Stien til den lokalt gemte licensnøgle, i %APPDATA% (skriv-sikkert
    når programmet kører som bygget EXE, i modsætning til projektmappen)."""
    appdata = Path(os.environ.get("APPDATA", Path.home()))
    folder = appdata / "JK-Draw"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "license_key.json"


def validate_key(hardware_id, key):
    """Verificerer at `key` er en gyldig signatur af `hardware_id`, lavet med
    den private nøgle. Kræver ikke selv nogen hemmelighed - den offentlige
    nøgle kan ikke bruges til at forfalske signaturer."""
    if not key:
        return False
    try:
        signature = base64.urlsafe_b64decode(key.encode("ascii"))
    except Exception:
        return False
    try:
        _PUBLIC_KEY.verify(signature, hardware_id.encode("utf-8"))
        return True
    except InvalidSignature:
        return False
    except Exception:
        return False


def load_saved_key():
    """Læser en tidligere gemt/valideret nøgle fra disk, hvis den findes."""
    license_path = get_license_path()
    if not license_path.exists():
        return None
    try:
        with open(license_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("key")
    except Exception:
        return None


def save_key(key):
    """Gemmer en valideret nøgle lokalt, så brugeren ikke skal indtaste den igen."""
    with open(get_license_path(), "w", encoding="utf-8") as f:
        json.dump({"key": key}, f)


def is_unlocked():
    """Tjekker om der allerede ligger en gyldig, gemt nøgle til denne maskine.

    Fejler "lukket" (låst) frem for at kaste en exception videre, så en
    uventet fejl her aldrig kan stoppe hele programmets opstart usynligt
    under pythonw.exe (ingen konsol til at vise fejlen)."""
    hardware_id = get_hardware_id()
    key = load_saved_key()
    try:
        return validate_key(hardware_id, key)
    except Exception:
        return False


def unlock_with_key(key):
    """Validerer en nyligt indtastet nøgle og gemmer den lokalt ved succes."""
    hardware_id = get_hardware_id()
    if validate_key(hardware_id, key):
        save_key(key)
        return True
    return False

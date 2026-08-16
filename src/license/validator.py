import hashlib
import hmac
import json
import os
import sys
from pathlib import Path

from .hardware import get_hardware_id

# src/ skal ligge på sys.path, så config.py (der ligger i src/ sammen med
# resten af programmets moduler) kan importeres uafhængigt af hvorfra
# license-pakken importeres fra.
_SRC_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _SRC_ROOT not in sys.path:
    sys.path.insert(0, _SRC_ROOT)

try:
    from config import SECRET
except ImportError:
    SECRET = None


def get_license_path():
    """Stien til den lokalt gemte licensnøgle, i %APPDATA% (skriv-sikkert
    når programmet kører som bygget EXE, i modsætning til projektmappen)."""
    appdata = Path(os.environ.get("APPDATA", Path.home()))
    folder = appdata / "JK-Draw"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "license_key.json"


def generate_key(hardware_id):
    """Genererer en HMAC-SHA256-nøgle bundet til det givne hardware-ID."""
    if not SECRET:
        raise RuntimeError(
            "SECRET er ikke sat. Udfyld SECRET i src/config.py."
        )
    return hmac.new(
        SECRET.encode("utf-8"),
        hardware_id.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def validate_key(hardware_id, key):
    """Tjekker om `key` er den korrekte nøgle for `hardware_id`."""
    if not key:
        return False
    expected = generate_key(hardware_id)
    return hmac.compare_digest(expected, key)


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
    """Tjekker om der allerede ligger en gyldig, gemt nøgle til denne maskine."""
    hardware_id = get_hardware_id()
    key = load_saved_key()
    return validate_key(hardware_id, key)


def unlock_with_key(key):
    """Validerer en nyligt indtastet nøgle og gemmer den lokalt ved succes."""
    hardware_id = get_hardware_id()
    if validate_key(hardware_id, key):
        save_key(key)
        return True
    return False

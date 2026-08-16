import hashlib
import uuid


def get_hardware_id():
    """Genererer et stabilt hardware-ID ud fra maskinens MAC-adresse."""
    mac = uuid.getnode()
    digest = hashlib.sha256(str(mac).encode("utf-8")).hexdigest()
    return digest[:16]

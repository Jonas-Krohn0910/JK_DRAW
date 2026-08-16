import base64
import os

from cryptography.hazmat.primitives import serialization

# src/private_key.pem findes KUN på udstederens (din) maskine - den er
# git-ignoreret og bliver aldrig distribueret til klienter. Uden den kan
# ingen generere gyldige licensnøgler, uanset hvad de ser i det offentlige
# repo (validator.py, som klienterne kører, indeholder kun den offentlige
# nøgle og kan udelukkende verificere, ikke signere).
_SRC_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_PRIVATE_KEY_PATH = os.path.join(_SRC_ROOT, "private_key.pem")


def _load_private_key():
    if not os.path.exists(_PRIVATE_KEY_PATH):
        raise RuntimeError(
            f"Privat nøgle mangler ({_PRIVATE_KEY_PATH}). Den findes kun på "
            "udstederens maskine og må aldrig committes til git."
        )
    with open(_PRIVATE_KEY_PATH, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def generate_key(hardware_id):
    """Signerer et hardware-ID med den private nøgle. Kan kun køre på en
    maskine der har src/private_key.pem."""
    private_key = _load_private_key()
    signature = private_key.sign(hardware_id.encode("utf-8"))
    return base64.urlsafe_b64encode(signature).decode("ascii")

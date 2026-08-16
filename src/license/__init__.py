from .hardware import get_hardware_id
from .validator import (
    validate_key,
    load_saved_key,
    save_key,
    is_unlocked,
    unlock_with_key,
    get_license_path,
)

# generate_key (signering) eksporteres bevidst IKKE herfra - den kræver
# src/private_key.pem, som kun findes på udstederens maskine. Importér den
# eksplicit fra license.keygen, så det er tydeligt i koden hvor den
# priviligerede handling sker.

__all__ = [
    "get_hardware_id",
    "validate_key",
    "load_saved_key",
    "save_key",
    "is_unlocked",
    "unlock_with_key",
    "get_license_path",
]

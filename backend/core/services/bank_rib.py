import re


def normalize_uemoa_rib(value: str) -> str:
    normalized = "".join(value.split()).upper()
    if not re.fullmatch(r"(?:BF|BJ|CI|GW|ML|NE|SN|TG)\d{22}", normalized):
        raise ValueError("Un RIB UEMOA complet de 24 caractères est requis.")
    return normalized


def rib_components(value: str) -> list[str]:
    return [value[:5], value[5:10], value[10:22], value[22:]]

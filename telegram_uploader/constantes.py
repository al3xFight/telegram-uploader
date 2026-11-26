"""Constantes y valores por defecto. No depende de ningún otro módulo del paquete."""
import sys
from pathlib import Path

VERSION = "1.4.0"

# Carpeta del proyecto (la que contiene subir_a_telegram.py), no la del paquete.
# Ahí se guardan config.json, la sesión de Telegram y el registro de subidos.


def calcular_directorio_base() -> Path:
    """Carpeta donde viven los datos del usuario (config, sesión y registro).

    En desarrollo es la carpeta del proyecto. Cuando el programa está empaquetado
    como ejecutable es la carpeta del .exe, para que los datos queden junto a él
    y no en una carpeta temporal.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


# Carpeta del proyecto (la que contiene subir_a_telegram.py), no la del paquete.
# Ahí se guardan config.json, la sesión de Telegram y el registro de subidos.
DIRECTORIO_BASE = calcular_directorio_base()
CONFIG_PATH = DIRECTORIO_BASE / "config.json"
SESSION_NAME = str(DIRECTORIO_BASE / "sesion_telegram")
REGISTRO_SUBIDOS = str(DIRECTORIO_BASE / "subidos.json")

EXTENSIONES_VIDEO = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".3gp"}
MAX_REINTENTOS_ERROR = 3
MAX_REINTENTOS_FLOOD = 5
UMBRAL_ARCHIVO_GRANDE = 10 * 1024 * 1024

CONFIG_DEFAULTS = {
    "idioma": "",
    "api_id": "",
    "api_hash": "",
    "canal": "",
    "chunks_paralelos": 8,
    "pausa_min": 3.0,
    "pausa_max": 6.0,
}

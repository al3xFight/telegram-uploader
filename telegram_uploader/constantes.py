"""Constantes y valores por defecto. No depende de ningún otro módulo del paquete."""
from pathlib import Path

VERSION = "1.2.0"

# Carpeta del proyecto (la que contiene subir_a_telegram.py), no la del paquete.
# Ahí se guardan config.json, la sesión de Telegram y el registro de subidos.
DIRECTORIO_BASE = Path(__file__).resolve().parent.parent
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

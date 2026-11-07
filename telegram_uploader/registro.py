"""Registro de archivos ya subidos (evita duplicados) y su clave de identificación."""
import hashlib
import json
import os
from pathlib import Path

from .consola import log
from .constantes import REGISTRO_SUBIDOS


def cargar_registro():
    if os.path.exists(REGISTRO_SUBIDOS):
        try:
            with open(REGISTRO_SUBIDOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            log.warning("⚠️  %s corrupto / corrupted, empezando registro nuevo / starting a new log.", REGISTRO_SUBIDOS)
            return {}
    return {}


def guardar_registro(registro):
    tmp = f"{REGISTRO_SUBIDOS}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(registro, f, indent=2, ensure_ascii=False)
    os.replace(tmp, REGISTRO_SUBIDOS)


def clave_archivo(ruta: Path) -> str:
    stat = ruta.stat()
    base = f"{ruta.name}-{stat.st_size}-{int(stat.st_mtime)}"
    return hashlib.sha256(base.encode()).hexdigest()

"""Consola y registro de eventos compartidos por todo el programa."""
import logging
import sys

from rich.console import Console
from rich.logging import RichHandler


def forzar_salida_utf8(flujo=None):
    """Fuerza UTF-8 en un flujo de salida (por defecto stdout y stderr).

    Con la salida redirigida en Windows (p. ej. `> salida.txt` bajo cp1252),
    el banner con emojis lanzaba UnicodeEncodeError (issue #24).
    """
    if flujo is None:
        for nombre in ("stdout", "stderr"):
            forzar_salida_utf8(getattr(sys, nombre, None))
        return None
    if not hasattr(flujo, "reconfigure"):
        return flujo
    try:
        flujo.reconfigure(encoding="utf-8", errors="replace")
    except (OSError, ValueError):
        pass
    return flujo


forzar_salida_utf8()

console = Console()

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
)
log = logging.getLogger("telegram_uploader")

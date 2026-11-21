"""Issue #24: la salida redirigida (p. ej. cp1252 en Windows) no debe lanzar UnicodeEncodeError."""
import io

from telegram_uploader import consola


def test_banner_con_emojis_en_salida_cp1252_no_lanza():
    """Simula `python subir_a_telegram.py > salida.txt` con la página de códigos cp1252."""
    flujo = io.TextIOWrapper(io.BytesIO(), encoding="cp1252", errors="strict")
    consola.forzar_salida_utf8(flujo)
    consola.console.file = flujo
    try:
        consola.console.print("[bold]📡 Telegram Uploader[/bold] — Banner 🚀 listo")
    finally:
        consola.console.file = None
    flujo.seek(0)
    salida = flujo.read()
    assert "Telegram Uploader" in salida
    assert "listo" in salida


def test_forzar_salida_utf8_reconfigura_codificacion():
    flujo = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    consola.forzar_salida_utf8(flujo)
    assert flujo.encoding == "utf-8"


def test_forzar_salida_utf8_tolerante_a_flujos_sin_reconfigure():
    class SinReconfigure:
        encoding = "cp1252"

    consola.forzar_salida_utf8(SinReconfigure())  # no debe lanzar

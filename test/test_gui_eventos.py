"""Los mensajes del registro llegan a la lista de eventos de la GUI."""
import logging

from telegram_uploader.consola import log
from telegram_uploader.gui_modelo import ManejadorEventos


def _capturar(emitir):
    recibidos = []
    manejador = ManejadorEventos(lambda nivel, texto: recibidos.append((nivel, texto)))
    nivel_anterior = log.level
    log.setLevel(logging.INFO)
    log.addHandler(manejador)
    try:
        emitir()
    finally:
        log.removeHandler(manejador)
        log.setLevel(nivel_anterior)
    return recibidos


def test_el_manejador_entrega_cada_mensaje_con_su_nivel():
    recibidos = _capturar(lambda: (log.info("hola"), log.warning("cuidado")))
    assert recibidos == [("INFO", "hola"), ("WARNING", "cuidado")]


def test_el_manejador_entrega_el_texto_ya_formateado():
    recibidos = _capturar(lambda: log.info("%s subido", "a.txt"))
    assert recibidos == [("INFO", "a.txt subido")]
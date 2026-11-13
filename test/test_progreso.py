"""El progreso se reporta mediante una interfaz, sin que subida.py dependa de Rich."""
import asyncio
from types import SimpleNamespace

from telegram_uploader import subida
from telegram_uploader.progreso import ReporteProgreso


class ReporteRegistrador(ReporteProgreso):
    """Reportero de prueba: guarda cada evento en orden."""

    def __init__(self):
        self.eventos = []
        self._siguiente = 0

    def iniciar_total(self, total):
        self.eventos.append(("total", total))

    def iniciar_archivo(self, nombre, total_bytes):
        self._siguiente += 1
        self.eventos.append(("inicio", nombre, total_bytes))
        return self._siguiente

    def actualizar_archivo(self, id_tarea, bytes_hechos):
        self.eventos.append(("avance", id_tarea, bytes_hechos))

    def terminar_archivo(self, id_tarea):
        self.eventos.append(("fin", id_tarea))

    def avanzar_total(self):
        self.eventos.append(("global",))


def test_reporte_base_no_hace_nada_y_sirve_como_contexto():
    with ReporteProgreso() as reporte:
        reporte.iniciar_total(3)
        tarea = reporte.iniciar_archivo("a.txt", 10)
        reporte.actualizar_archivo(tarea, 5)
        reporte.terminar_archivo(tarea)
        reporte.avanzar_total()


def test_callback_de_progreso_solo_avanza():
    reporte = ReporteRegistrador()
    ctx = SimpleNamespace(reporte=reporte)
    callback = subida.crear_callback_progreso(ctx, 7)
    callback(10, 100)
    callback(10, 100)
    callback(30, 100)
    assert reporte.eventos == [("avance", 7, 10), ("avance", 7, 30)]


def test_simulacion_avanza_el_total():
    reporte = ReporteRegistrador()
    assert subida.simular_subida(SimpleNamespace(reporte=reporte)) is True
    assert reporte.eventos == [("global",)]


def test_ejecutar_subidas_reporta_total_y_avance_global(tmp_path):
    rutas = []
    for nombre in ("a.txt", "b.txt"):
        ruta = tmp_path / nombre
        ruta.write_text("x")
        rutas.append(ruta)
    reporte = ReporteRegistrador()
    opciones = subida.OpcionesSubida(dry_run=True)

    subidos = asyncio.run(subida.ejecutar_subidas(None, None, rutas, {}, opciones, reporte))

    assert subidos == 0  # en simulación no se registra nada
    assert reporte.eventos == [("total", 2), ("global",), ("global",)]
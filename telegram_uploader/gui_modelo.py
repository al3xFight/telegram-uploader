"""Lógica de la interfaz gráfica que no necesita pantalla.

No importa Flet: así se prueba con pytest y en la integración continua.
Solo `gui.py` dibuja la ventana.
"""
from dataclasses import dataclass, field
from typing import Callable

from .progreso import ReporteProgreso


@dataclass
class TareaArchivo:
    """Avance de un archivo que se está subiendo."""

    nombre: str
    total: int
    hechos: int = 0

    @property
    def porcentaje(self) -> float:
        if self.total <= 0:
            return 0.0
        return self.hechos * 100 / self.total


@dataclass
class EstadoProgreso:
    """Lo que la pantalla necesita para dibujar el avance."""

    total_archivos: int = 0
    completados: int = 0
    archivos: dict = field(default_factory=dict)  # id de tarea -> TareaArchivo


class ReporteEstado(ReporteProgreso):
    """Guarda el avance en datos simples y avisa a la pantalla cada vez que cambia."""

    def __init__(self, al_cambiar: Callable):
        self.estado = EstadoProgreso()
        self._al_cambiar = al_cambiar
        self._siguiente_id = 0

    def _avisar(self) -> None:
        self._al_cambiar(self.estado)

    def iniciar_total(self, total):
        self.estado.total_archivos = total
        self._avisar()

    def iniciar_archivo(self, nombre, total_bytes):
        self._siguiente_id += 1
        self.estado.archivos[self._siguiente_id] = TareaArchivo(nombre, total_bytes)
        self._avisar()
        return self._siguiente_id

    def actualizar_archivo(self, id_tarea, bytes_hechos):
        self.estado.archivos[id_tarea].hechos = bytes_hechos
        self._avisar()

    def terminar_archivo(self, id_tarea):
        self.estado.archivos.pop(id_tarea, None)
        self._avisar()

    def avanzar_total(self):
        self.estado.completados += 1
        self._avisar()

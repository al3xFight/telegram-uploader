"""Lógica de la interfaz gráfica que no necesita pantalla.

No importa Flet: así se prueba con pytest y en la integración continua.
Solo `gui.py` dibuja la ventana.
"""
from dataclasses import dataclass, field
from functools import partial
from typing import Callable

from .progreso import ReporteProgreso
from .servicio import CallbacksLogin


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

class PuenteLogin:
    """Conecta los datos que pide Telethon al iniciar sesión con los diálogos de la pantalla.

    `pedir` es una función asíncrona que recibe la clave del dato ("telefono", "codigo"
    o "contrasena") y devuelve lo que escribió la persona. El puente no guarda ni
    registra esos valores: solo los entrega a Telethon (riesgo R11).
    """

    def __init__(self, pedir: Callable):
        self._pedir = pedir

    def callbacks(self) -> CallbacksLogin:
        return CallbacksLogin(
            telefono=partial(self._pedir, "telefono"),
            codigo=partial(self._pedir, "codigo"),
            contrasena=partial(self._pedir, "contrasena"),
        )

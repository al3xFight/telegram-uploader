"""Lógica de la interfaz gráfica que no necesita pantalla.

No importa Flet: así se prueba con pytest y en la integración continua.
Solo `gui.py` dibuja la ventana.
"""
from dataclasses import dataclass, field
from functools import partial
import logging
import math
from typing import Callable

from .config import config_incompleta
from .errores import ErrorDeUso
from .progreso import ReporteProgreso
from .servicio import CallbacksLogin, Solicitud, resolver_ajustes, validar_carpeta


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

def fraccion_total(estado: EstadoProgreso) -> float:
    """Avance global entre 0 y 1, para la barra de progreso total."""
    if estado.total_archivos <= 0:
        return 0.0
    return min(1.0, estado.completados / estado.total_archivos)


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

def _texto_obligatorio(campos: dict, campo: str) -> str:
    valor = str(campos.get(campo, "")).strip()
    if not valor:
        raise ErrorDeUso("err_required", campo=campo)
    return valor


def _entero(campos: dict, campo: str, clave_error: str = "err_invalid_number") -> int:
    try:
        return int(str(campos.get(campo, "")).strip())
    except ValueError:
        raise ErrorDeUso(clave_error, campo=campo) from None


def _decimal(campos: dict, campo: str) -> float:
    try:
        valor = float(str(campos.get(campo, "")).strip())
    except ValueError:
        raise ErrorDeUso("err_invalid_number", campo=campo) from None
    if not math.isfinite(valor):  # rechaza "nan" e "inf"
        raise ErrorDeUso("err_invalid_number", campo=campo)
    return valor


def validar_formulario(campos: dict) -> dict:
    """Convierte y valida lo escrito en el formulario de configuración.

    Devuelve los valores con su tipo; lanza ErrorDeUso (con el nombre del campo en
    `datos["campo"]`) si algo es inválido. El api_hash nunca aparece en un error.
    """
    api_id = _entero(campos, "api_id", "err_api_id_numeric")
    api_hash = _texto_obligatorio(campos, "api_hash")
    canal = _texto_obligatorio(campos, "canal")
    chunks = _entero(campos, "chunks_paralelos")
    if chunks < 1:
        raise ErrorDeUso("err_chunks_min1", campo="chunks_paralelos")

    pausas = {nombre: _decimal(campos, nombre) for nombre in ("pausa_min", "pausa_max")}
    for nombre, valor in pausas.items():
        if valor < 0:
            raise ErrorDeUso("err_pausas_negative", campo=nombre)

    return {"api_id": api_id, "api_hash": api_hash, "canal": canal,
            "chunks_paralelos": chunks, **pausas}

class ManejadorEventos(logging.Handler):
    """Entrega cada mensaje del registro (nivel y texto ya formateado) a la pantalla."""

    def __init__(self, al_mensaje: Callable):
        super().__init__()
        self._al_mensaje = al_mensaje

    def emit(self, record: logging.LogRecord) -> None:
        self._al_mensaje(record.levelname, record.getMessage())

@dataclass(frozen=True)
class AjustesVentana:
    """Lo que se elige en la pantalla de subida. Cumple lo que pide `resolver_ajustes`."""

    solo_videos: bool = True
    borrar_local: bool = False
    dry_run: bool = False
    paralelo: int = 1
    chunks_paralelos: int | None = None  # None: usar la configuración guardada
    pausa_min: float | None = None
    pausa_max: float | None = None


def necesita_confirmacion(ajustes: AjustesVentana) -> bool:
    """Borrar archivos de verdad exige confirmación explícita; en simulación no."""
    return ajustes.borrar_local and not ajustes.dry_run


def crear_solicitud(config: dict, carpeta: str, ajustes: AjustesVentana) -> Solicitud:
    """Arma la solicitud de subida con las mismas validaciones que la consola."""
    if config_incompleta(config):
        raise ErrorDeUso("gui_err_config_incompleta")
    if not str(carpeta).strip():
        raise ErrorDeUso("gui_err_sin_carpeta")
    ruta = validar_carpeta(str(carpeta).strip())
    api_id, api_hash, canal, opciones = resolver_ajustes(ajustes, config)
    return Solicitud(api_id, api_hash, canal, ruta, ajustes.solo_videos, opciones)

"""Flujo completo de subida, sin depender de la consola.

Lo usan tanto la línea de comandos como la interfaz gráfica: cada una prepara
una Solicitud, elige su reportero de progreso y, si quiere, sus funciones de login.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .consola import log
from .i18n import t
from .medios import encontrar_archivos, obtener_timestamp_orden
from .progreso import ReporteProgreso
from .registro import cargar_registro, clave_archivo
from .subida import OpcionesSubida, crear_cliente, ejecutar_subidas, resolver_destino


@dataclass(frozen=True)
class Solicitud:
    """Qué se va a subir y con qué cuenta."""

    api_id: int
    api_hash: str
    canal: str
    carpeta: Path
    solo_videos: bool
    opciones: OpcionesSubida


@dataclass(frozen=True)
class CallbacksLogin:
    """Funciones que Telethon llama para pedir teléfono, código y contraseña de 2FA."""

    telefono: Callable
    codigo: Callable
    contrasena: Callable

    def para_telethon(self) -> dict:
        return {"phone": self.telefono, "code_callback": self.codigo,
                "password": self.contrasena}


@dataclass(frozen=True)
class ResultadoSubida:
    encontrados: int = 0
    pendientes: int = 0
    subidos: int = 0


def buscar_pendientes(carpeta: Path, solo_videos: bool, registro: dict):
    """Devuelve (todos_los_archivos, pendientes), ambos en orden cronológico."""
    archivos = list(encontrar_archivos(carpeta, solo_videos=solo_videos))
    archivos.sort(key=obtener_timestamp_orden)
    pendientes = [a for a in archivos if clave_archivo(a) not in registro]
    return archivos, pendientes


async def ejecutar_servicio(solicitud: Solicitud, reporte: ReporteProgreso,
                            login: CallbacksLogin | None = None) -> ResultadoSubida:
    """Busca los pendientes, inicia sesión, sube y devuelve cuántos se subieron.

    Sin `login`, Telethon pide teléfono y código por consola, como siempre.
    """
    registro = cargar_registro()
    archivos, pendientes = buscar_pendientes(
        solicitud.carpeta, solicitud.solo_videos, registro)
    log.info(t("log_found_files", n=len(archivos)))
    log.info(t("log_pending_files", n=len(pendientes)))
    if not pendientes:
        log.info(t("log_nothing_new"))
        return ResultadoSubida(len(archivos), 0, 0)

    client = crear_cliente(solicitud.api_id, solicitud.api_hash)
    subidos = 0
    try:
        await client.start(**(login.para_telethon() if login else {}))
        destino = await resolver_destino(client, solicitud.canal)
        subidos = await ejecutar_subidas(
            client, destino, pendientes, registro, solicitud.opciones, reporte)
        log.info(t("log_finished", ok=subidos, total=len(pendientes)))
    except KeyboardInterrupt:
        log.warning(t("log_interrupted"))
    finally:
        await client.disconnect()
    return ResultadoSubida(len(archivos), len(pendientes), subidos)

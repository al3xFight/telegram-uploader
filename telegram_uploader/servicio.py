"""Flujo completo de subida, sin depender de la consola.

Lo usan tanto la línea de comandos como la interfaz gráfica: cada una prepara
una Solicitud, elige su reportero de progreso y, si quiere, sus funciones de login.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .consola import log
from .errores import ErrorDeUso
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

def validar_carpeta(ruta) -> Path:
    """Comprueba que la carpeta exista; lanza ErrorDeUso si no."""
    carpeta = Path(ruta).expanduser()
    if not carpeta.is_dir():
        raise ErrorDeUso("err_carpeta_not_found", carpeta=carpeta)
    return carpeta


def resolver_ajustes(args, config: dict):
    """Combina la configuración guardada y los ajustes de la ejecución; valida.

    `args` es cualquier objeto con chunks_paralelos, pausa_min y pausa_max (None para usar
    la configuración), borrar_local, dry_run y paralelo: los argumentos de la consola o los
    de la ventana. Lanza ErrorDeUso si algo es inválido.
    Devuelve (api_id, api_hash, canal, opciones).
    """
    try:
        api_id = int(config["api_id"])
    except (TypeError, ValueError):
        raise ErrorDeUso("err_api_id_invalid_saved") from None

    chunks_paralelos = args.chunks_paralelos if args.chunks_paralelos is not None else int(config["chunks_paralelos"])
    pausa_min = args.pausa_min if args.pausa_min is not None else float(config["pausa_min"])
    pausa_max = args.pausa_max if args.pausa_max is not None else float(config["pausa_max"])

    if chunks_paralelos < 1:
        raise ErrorDeUso("err_chunks_min1")
    if pausa_min < 0 or pausa_max < 0:
        raise ErrorDeUso("err_pausas_negative")
    if pausa_max > 0 and pausa_min > pausa_max:
        pausa_min, pausa_max = pausa_max, pausa_min

    opciones = OpcionesSubida(
        borrar_local=args.borrar_local, dry_run=args.dry_run,
        pausa_min=pausa_min, pausa_max=pausa_max, chunks_paralelos=chunks_paralelos,
        archivos_simultaneos=args.paralelo,
    )
    return api_id, str(config["api_hash"]), config["canal"], opciones

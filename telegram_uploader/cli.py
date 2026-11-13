"""Interfaz de línea de comandos: argumentos y flujo principal del programa."""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

from rich.panel import Panel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from .progreso import ReporteProgreso

from .config import (
    asegurar_configuracion,
    cargar_config,
    config_existe,
    ejecutar_modo_config,
)
from .consola import console, log
from .constantes import VERSION
from .errores import ErrorDeUso
from .i18n import elegir_idioma_interactivo, t, traductor
from .medios import FFMPEG_DISPONIBLE
from .servicio import Solicitud, ejecutar_servicio
from .subida import (
    OpcionesSubida,
)


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=t("arg_desc"), epilog=t("arg_epilog"))
    parser.add_argument("--config", action="store_true", help=t("arg_config_help"))
    parser.add_argument("--carpeta", default=None, help=t("arg_carpeta_help"))
    parser.add_argument("--todo", action="store_true", help=t("arg_todo_help"))
    parser.add_argument("--borrar-local", action="store_true", help=t("arg_borrar_local_help"))
    parser.add_argument("--paralelo", type=int, default=1, help=t("arg_paralelo_help"))
    parser.add_argument("--chunks-paralelos", type=int, default=None, help=t("arg_chunks_help"))
    parser.add_argument("--pausa-min", type=float, default=None, help=t("arg_pausa_min_help"))
    parser.add_argument("--pausa-max", type=float, default=None, help=t("arg_pausa_max_help"))
    parser.add_argument("--dry-run", action="store_true", help=t("arg_dry_run_help"))
    parser.add_argument("--debug", action="store_true", help=t("arg_debug_help"))
    parser.add_argument("--lang", choices=["es", "en"], default=None, help=t("arg_lang_help"))
    parser.add_argument("--version", action="version", version=f"Telegram Uploader {VERSION}")
    return parser


def configurar_idioma(config: dict, argv: list) -> None:
    """Fija el idioma activo. Prioridad: --lang (temporal) > config guardada > preguntar."""
    lang_cli = None
    if "--lang" in argv:
        idx = argv.index("--lang")
        if idx + 1 < len(argv):
            lang_cli = argv[idx + 1]

    if lang_cli in ("es", "en"):
        traductor.idioma = lang_cli
    elif config.get("idioma") in ("es", "en"):
        traductor.idioma = config["idioma"]
    elif "-h" in argv or "--help" in argv:
        traductor.idioma = "es"  # --help no debe quedar esperando input
    else:
        traductor.idioma = elegir_idioma_interactivo()
        if not config_existe():
            config["idioma"] = traductor.idioma  # se confirma al guardar el resto en el wizard


def mostrar_banner() -> None:
    console.print(Panel.fit(
        f"[bold]📡 Telegram Uploader[/bold] [dim]v{VERSION}[/dim]\n{t('banner_subtitle')}",
        border_style="blue",
    ))


def resolver_ajustes(args, config: dict):
    """Combina configuración guardada y argumentos; lanza ErrorDeUso si algo es inválido.

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


def mostrar_avisos(args) -> None:
    """Avisos no bloqueantes sobre el entorno y las opciones elegidas."""
    if args.paralelo > 1:
        log.warning(t("warn_paralelo_order", n=args.paralelo))

    try:
        import cryptg  # noqa: F401
    except ImportError:
        log.warning(t("tip_cryptg"))

    if not FFMPEG_DISPONIBLE:
        log.warning(t("warn_ffmpeg_missing"))


def validar_carpeta(ruta) -> Path:
    """Comprueba que la carpeta exista; lanza ErrorDeUso si no."""
    carpeta = Path(ruta).expanduser()
    if not carpeta.is_dir():
        raise ErrorDeUso("err_carpeta_not_found", carpeta=carpeta)
    return carpeta


def obtener_carpeta(ruta_indicada) -> Path:
    """Pide la carpeta por consola si no se indicó, y comprueba que exista."""
    ruta_carpeta = ruta_indicada
    while not ruta_carpeta:
        ruta_carpeta = input(f"{t('prompt_carpeta')}: ").strip().strip('"').strip("'")
    return validar_carpeta(ruta_carpeta)

class ReporteRich(ReporteProgreso):
    """Barra de progreso de la consola (rich)."""

    def __init__(self):
        self._progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=None),
            TaskProgressColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TextColumn("[dim]Elapsed:[/dim]"),
            TimeElapsedColumn(),
            TextColumn("[dim]ETA:[/dim]"),
            TimeRemainingColumn(),
            transient=False,
            refresh_per_second=10,
        )
        self._id_total = None

    def __enter__(self):
        self._progress.__enter__()
        return self

    def __exit__(self, *excepcion):
        return self._progress.__exit__(*excepcion)

    def iniciar_total(self, total):
        self._id_total = self._progress.add_task(t("progress_total_label"), total=total)

    def iniciar_archivo(self, nombre, total_bytes):
        return self._progress.add_task(f"🎬 {nombre[:25].ljust(25)}", total=total_bytes)

    def actualizar_archivo(self, id_tarea, bytes_hechos):
        self._progress.update(id_tarea, completed=bytes_hechos)

    def terminar_archivo(self, id_tarea):
        self._progress.remove_task(id_tarea)

    def avanzar_total(self):
        if self._id_total is not None:
            self._progress.advance(self._id_total, 1)

async def flujo_principal():
    config = cargar_config()
    configurar_idioma(config, sys.argv)
    mostrar_banner()

    args = construir_parser().parse_args()
    if args.debug:
        log.setLevel(logging.DEBUG)

    if args.config:
        ejecutar_modo_config(config)
        return

    config = asegurar_configuracion(config)
    api_id, api_hash, canal, opciones = resolver_ajustes(args, config)
    mostrar_avisos(args)

    carpeta = obtener_carpeta(args.carpeta)
    solicitud = Solicitud(
        api_id=api_id,
        api_hash=api_hash,
        canal=canal,
        carpeta=carpeta,
        solo_videos=not args.todo,
        opciones=opciones,
    )
    await ejecutar_servicio(solicitud, ReporteRich())

async def main():
    """Ejecuta el flujo y convierte los errores de uso en un mensaje y código de salida 1."""
    try:
        await flujo_principal()
    except ErrorDeUso as e:
        console.print(f"[red]{t(e.clave, **e.datos)}[/red]")
        for pista in e.pistas:
            console.print(t(pista))
        sys.exit(1)

def ejecutar() -> None:
    """Punto de entrada: lanza el programa principal."""
    asyncio.run(main())
